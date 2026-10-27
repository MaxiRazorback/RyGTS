@echo off
rem Builds ryGT_dlss.dll, ryGT's optional DLSS plugin, with clang-cl and the MSVC libraries.
rem Usage: build.cmd [output folder]
rem   DLSS_SDK        NVIDIA's DLSS SDK (github.com/NVIDIA/DLSS: include\ and lib\Windows_x86_64\x64\)
rem   VULKAN_INCLUDE  Vulkan headers (default: shadGT's externals\vulkan-headers\include next to RyGT)
setlocal
set OUT=%~1
if "%OUT%"=="" set OUT=%~dp0out
if "%DLSS_SDK%"=="" set DLSS_SDK=E:\Development\dlss\sdk
if "%VULKAN_INCLUDE%"=="" set VULKAN_INCLUDE=%~dp0..\..\..\shadGT\externals\vulkan-headers\include
if not exist "%DLSS_SDK%\include\nvsdk_ngx_vk.h" (echo DLSS SDK not found in %DLSS_SDK% & exit /b 1)
if not exist "%VULKAN_INCLUDE%\vulkan\vulkan.h" (echo Vulkan headers not found in %VULKAN_INCLUDE% & exit /b 1)
set VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat
if exist "%VCVARS%" call "%VCVARS%" >nul
if not exist "%OUT%" mkdir "%OUT%"
clang-cl /nologo /O2 /MD /EHsc /std:c++17 /DVK_NO_PROTOTYPES /DWIN32_LEAN_AND_MEAN /DNOMINMAX ^
    /I"%DLSS_SDK%\include" /I"%VULKAN_INCLUDE%" /I"%~dp0." ^
    "%~dp0ryGT_dlss.cpp" /LD /Fe"%OUT%\ryGT_dlss.dll" /Fo"%OUT%\ryGT_dlss.obj" ^
    /link "%DLSS_SDK%\lib\Windows_x86_64\x64\nvsdk_ngx_d.lib" advapi32.lib user32.lib
