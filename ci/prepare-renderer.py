"""Reconstruct the published development renderer; fail on any patch mismatch."""
import argparse
from pathlib import Path
import subprocess

BASE = "1d13c88d2e57bc63ce1586fe0b8f3342b6afdd19"
REPOSITORY = "https://gitlab.com/rygt-team/ShadGT.git"


def run(*args):
    subprocess.run(args, check=True)


def prepare(destination):
    root = Path(__file__).resolve().parent.parent
    destination = Path(destination).resolve()
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite existing source: {destination}")
    run("git", "init", str(destination))
    run("git", "-C", str(destination), "config", "core.longpaths", "true")
    run("git", "-C", str(destination), "remote", "add", "origin", REPOSITORY)
    run("git", "-C", str(destination), "fetch", "--depth=1", "origin", BASE)
    run("git", "-C", str(destination), "checkout", "--detach", "FETCH_HEAD")
    patches = root / "renderer" / "shadGT-patches"
    camera = patches / "0065-in-game-camera-manager.patch"
    ordered = [camera, patches / "0020-fix-dlss-temporal-scene-reconstruction.patch"]
    ordered += sorted(p for p in patches.glob("*.patch")
                      if p != camera and 62 <= int(p.name[:4]) <= 99)
    applied = []
    for patch in ordered:
        command = ["git", "-C", str(destination), "apply", "--whitespace=nowarn"]
        if patch.name.startswith("0064-"):
            run(*command, "--exclude=ryty_gpu/ryty_entry.cpp", str(patch))
            run(*command, str(root / "ci" / "renderer-0064-camera-entry.patch"))
        else:
            run(*command, str(patch))
        applied.append(patch.name)
    (destination / "CI-SOURCE.txt").write_text(
        REPOSITORY + "\n" + BASE + "\n" + "\n".join(applied) + "\n", encoding="utf-8")
    run("git", "-C", str(destination), "-c", "core.longpaths=true", "submodule", "update", "--init", "--recursive", "--jobs", "4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    prepare(parser.parse_args().destination)
