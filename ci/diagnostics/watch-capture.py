"""Wait for the game in this Debug runtime, then arm the hash-checked capture helper."""
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import sys
import time

if sys.version_info < (3, 12):
    raise SystemExit('Python 3.12 or newer is required for the optional capture tools.')

root = Path(__file__).resolve().parents[2]
expected = str((root / 'GTSport.exe').resolve()).casefold()
user = ctypes.WinDLL('user32', use_last_error=True)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user.IsWindowVisible.argtypes = [wintypes.HWND]
callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user.EnumWindows.argtypes = [callback, wintypes.LPARAM]
user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
print('Press Play in the Debug launcher. Waiting for this Debug game window...', flush=True)
deadline = time.monotonic() + 1200
while time.monotonic() < deadline:
    found = []
    @callback
    def inspect(window, _):
        if not user.IsWindowVisible(window): return True
        title = ctypes.create_unicode_buffer(512)
        user.GetWindowTextW(window, title, len(title))
        if 'Gran Turismo' not in title.value: return True
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(window, ctypes.byref(pid))
        handle = kernel.OpenProcess(0x1000, False, pid.value)
        if not handle: return True
        try:
            path = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(path))
            if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and path.value.casefold() == expected:
                found.append(pid.value)
        finally: kernel.CloseHandle(handle)
        return True
    user.EnumWindows(inspect, 0)
    if found:
        print('F8: native frame; Ctrl+F8: performance recording; Shift+F8: visible burst.', flush=True)
        raise SystemExit(subprocess.call([sys.executable, str(Path(__file__).with_name('frame-capture-hotkey.py')), str(found[0])], cwd=root))
    time.sleep(1)
raise SystemExit('No Debug game window found within 20 minutes.')
