"""Dispatch a pinned GitHub Windows workflow and return its artifacts to GitLab."""
import datetime
import atexit
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import signal
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise RuntimeError("Refusing non-HTTPS artifact redirect")
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            result.remove_header("Authorization")
        return result


def unpack(archive, destination, expected):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if sum(e.file_size for e in entries) > 2 * 1024**3:
            raise RuntimeError("Artifact exceeds unpacked size limit")
        names = set()
        for entry in entries:
            name = entry.filename.replace("\\", "/")
            path = PurePosixPath(name)
            if (path.is_absolute() or ".." in path.parts or ":" in name
                    or not path.parts or path.parts[0] not in {"launcher", "renderer", "GITHUB-BUILD.json"}
                    or stat.S_ISLNK(entry.external_attr >> 16) or name in names):
                raise RuntimeError("Unsafe or duplicate artifact path")
            names.add(name)
            (destination / name).resolve().relative_to(destination)
        metadata = json.loads(bundle.read("GITHUB-BUILD.json"))
        for key, value in expected.items():
            if str(metadata.get(key)) != str(value):
                raise RuntimeError(f"Artifact provenance mismatch: {key}")
        for folder, executable in [("launcher", "RyGT.exe"), ("renderer", "libSceVideoOut.prx")]:
            revision = bundle.read(f"{folder}/RYGT-COMMIT.txt").decode("utf-8-sig").strip()
            if revision != expected["gitlab_commit"]:
                raise RuntimeError("Artifact source revision mismatch")
            checksums = {}
            for line in bundle.read(f"{folder}/SHA256SUMS.txt").decode("utf-8-sig").splitlines():
                digest, filename = line.split("  ", 1)
                if not re.fullmatch(r"[0-9a-fA-F]{64}", digest) or not re.fullmatch(r"[^/\\:]+", filename):
                    raise RuntimeError("Invalid artifact checksum entry")
                data = bundle.read(f"{folder}/{filename}")
                if hashlib.sha256(data).hexdigest() != digest.lower():
                    raise RuntimeError("Artifact checksum mismatch")
                checksums[filename] = digest
            if executable not in checksums or bundle.read(f"{folder}/{executable}")[:2] != b"MZ":
                raise RuntimeError("Missing Windows build output")
        # Validate the entire archive before extracting any member.
        bundle.extractall(destination)


def main():
    config = json.loads(Path("ci/github-actions.json").read_text())
    token = os.environ.get("GITHUB_ACTIONS_TOKEN")
    if not token:
        raise SystemExit("Set masked GitLab variable GITHUB_ACTIONS_TOKEN: CI repository Actions read/write only")
    repository = config["repository"]
    revision = os.environ["CI_COMMIT_SHA"]
    workflow_commit = config["workflow_commit"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise SystemExit("Invalid GitHub repository")
    if not all(re.fullmatch(r"[0-9a-f]{40}", x) for x in [revision, workflow_commit]):
        raise SystemExit("Full source/workflow commit pins are required")
    request_id = f'{os.environ["CI_PIPELINE_ID"]}-{os.environ["CI_JOB_ID"]}-{uuid.uuid4().hex}'
    api = f"https://api.github.com/repos/{repository}"
    opener = urllib.request.build_opener(SafeRedirect())

    def request(path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(api + path, data=data, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RyGT-GitLab-CI", "Content-Type": "application/json"})
        for attempt in range(4):
            try:
                return opener.open(req, timeout=60)
            except urllib.error.HTTPError as error:
                # Never retry a dispatch POST: it could start duplicate builds.
                if body is not None or error.code not in {429, 500, 502, 503, 504} or attempt == 3:
                    raise
                time.sleep(min(60, 5 * (attempt + 1)))

    started = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    with request(f'/actions/workflows/{config["workflow"]}/dispatches', {
            "ref": config["ref"], "inputs": {"source_sha": revision, "request_id": request_id}}):
        pass
    print(f"Dispatched {repository}: {request_id}", flush=True)
    deadline = time.monotonic() + 3.5 * 3600
    run = None
    def cancel_on_exit():
        if run and run["status"] != "completed":
            try:
                with request(f'/actions/runs/{run["id"]}/cancel', {}):
                    pass
            except (urllib.error.URLError, TimeoutError):
                print("Could not cancel unfinished GitHub run; inspect its URL", flush=True)
    atexit.register(cancel_on_exit)
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, terminate)
    while time.monotonic() < deadline:
        if run is None:
            query = urllib.parse.urlencode({"event": "workflow_dispatch", "branch": config["ref"],
                "per_page": 100, "created": ">=" + started.isoformat()})
            with request(f'/actions/workflows/{config["workflow"]}/runs?{query}') as response:
                runs = json.load(response)["workflow_runs"]
            matches = [r for r in runs if r["display_title"] == "gitlab-" + request_id]
            if len(matches) > 1:
                raise RuntimeError("Ambiguous workflow dispatch")
            if matches:
                run = matches[0]
                if run["head_sha"] != workflow_commit:
                    raise RuntimeError("Workflow changed: review and update ci/github-actions.json")
                print("GitHub run: " + run["html_url"], flush=True)
        else:
            with request(f'/actions/runs/{run["id"]}') as response:
                run = json.load(response)
        if run and run["status"] == "completed":
            break
        time.sleep(15)
    else:
        raise RuntimeError("GitHub build wait timed out")
    if run["conclusion"] != "success":
        raise RuntimeError(f'GitHub build {run["conclusion"]}: {run["html_url"]}')
    with request(f'/actions/runs/{run["id"]}/artifacts?per_page=100') as response:
        artifacts = json.load(response)["artifacts"]
    matches = [a for a in artifacts if a["name"] == "windows-" + request_id and not a["expired"]]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one matching Windows artifact")
    artifact = matches[0]
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "windows.zip"
        with request(f'/actions/artifacts/{artifact["id"]}/zip') as response, archive.open("wb") as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 2 * 1024**3:
                    raise RuntimeError("Artifact download exceeds size limit")
                output.write(chunk)
        digest = artifact.get("digest")
        if digest and digest != "sha256:" + hashlib.file_digest(archive.open("rb"), "sha256").hexdigest():
            raise RuntimeError("GitHub artifact digest mismatch")
        unpack(archive, "artifacts", {"gitlab_commit": revision, "request_id": request_id,
            "github_run_id": str(run["id"]), "workflow_commit": workflow_commit})
    print("Verified Windows artifacts returned to this GitLab pipeline", flush=True)


if __name__ == "__main__":
    main()
