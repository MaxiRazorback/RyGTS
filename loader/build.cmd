@echo off
rem Builds RyGT.exe (the loader) with the C# compiler that ships with Windows' .NET Framework 4.x.
rem Usage: build.cmd [output folder] [Release|Diagnostics]
setlocal
set OUT=%~1
if "%OUT%"=="" set OUT=%~dp0
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
set SYMBOLS=
if /i "%~2"=="Diagnostics" set SYMBOLS=/debug:full /pdb:"%OUT%\RyGT.pdb"
"%CSC%" /nologo /target:winexe /optimize+ %SYMBOLS% /win32icon:"%~dp0ryGT.ico" /resource:"%~dp0ryGT.ico",ryGT.ico /out:"%OUT%\RyGT.exe" ^
    /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ^
    "%~dp0RenderResolution.cs" "%~dp0ShaderCacheIdentity.cs" "%~dp0VulkanDevices.cs" "%~dp0RyGTLoader.cs" "%~dp0ControlsForm.cs" "%~dp0PortsForm.cs" "%~dp0Logging.cs" "%~dp0WheelForm.cs"
