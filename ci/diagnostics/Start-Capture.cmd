@echo off
where py.exe >nul 2>nul
if not errorlevel 1 (
  py.exe -3 "%~dp0watch-capture.py"
) else (
  where python.exe >nul 2>nul
  if errorlevel 1 (
    echo Python 3.12 or newer is required for the optional capture tools.
    echo The Debug renderer still records its normal diagnostics without this tool.
    pause
    exit /b 1
  )
  python.exe "%~dp0watch-capture.py"
)
