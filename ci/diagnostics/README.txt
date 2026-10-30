Optional diagnostics tools

Run Start-Capture.cmd with Python 3.12 or newer installed, then press Play in
the Debug launcher and focus the game. The collector accepts only this Debug
runtime's executable and verifies the loaded renderer and code guards before
requesting a native capture. It does not attach a debugger or suspend threads.

F8 captures graphics inputs, shader passes, CPU/GPU timestamp spans and mip data.
Ctrl+F8 starts/stops a performance interval. Shift+F8 captures a visible burst.
See the Debug folder's README.txt for limitations and offline analysis commands.
