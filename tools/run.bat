@echo off
REM ============================================
REM WeChat Video Face Classification System - Run Script
REM ============================================

setlocal enabledelayedexpansion

REM FFmpeg 路径
set FFMPEG_PATH=E:\local\ffmpeg\bin\ffmpeg.exe
set FFPROBE_PATH=E:\local\ffmpeg\bin\ffprobe.exe

REM ============================================
REM GPU Configuration (默认 True，用环境变量覆盖)
REM ============================================
REM 不设置则默认使用 GPU。要强制使用 CPU 可设：set USE_GPU=0
REM set USE_GPU=1
REM set USE_GPU=0

REM Get script directory without trailing backslash
for %%i in ("%~dp0.") do set "SCRIPT_DIR=%%~fi"

echo.
echo ============================================
echo WeChat Video Face Classification System
echo ============================================
echo.
set "ROOT_DIR=%SCRIPT_DIR%\.."


REM 视频目录，必须在web目录下！
set VIDEO_DIR=%ROOT_DIR%\web\data

REM 微信数据目录
@REM cd tools
@REM mklink /J ..\web\data E:\local\home\xwechat_files\winseliu_f4ec\msg\video\2026-02

REM Python 虚拟环境 (conda)
set CONDA_DEFAULT_ENV=video

REM call conda activate video


echo ROOT_DIR: %ROOT_DIR%
echo VIDEO_DIR: %VIDEO_DIR%
echo.

REM Detect and verify Python environment via Conda info
set "FINAL_PYTHON="

REM 1. Check 'conda info' for the truly active environment
set "ACTUAL_CONDA_ENV=None"
for /f "tokens=2 delims=:" %%a in ('conda info 2^>nul ^| findstr /c:"active environment :"') do (
    set "TEMP_ENV=%%a"
    REM Remove leading/trailing spaces
    for /f "tokens=*" %%g in ("!TEMP_ENV!") do set "ACTUAL_CONDA_ENV=%%g"
)

if /i "!ACTUAL_CONDA_ENV!"=="%CONDA_DEFAULT_ENV%" (
    set "FINAL_PYTHON=python"
    echo - Verified: Conda reports active environment is '%CONDA_DEFAULT_ENV%'.
)

REM 2. Fallback to hardcoded path if not active
if not defined FINAL_PYTHON (
    if exist "%PYTHON_PATH%" (
        echo - Warning: Current environment is "!ACTUAL_CONDA_ENV!", not '%CONDA_DEFAULT_ENV%'.
        echo - Attempting to use absolute path: %PYTHON_PATH%
        "%PYTHON_PATH%" -V >nul 2>&1
        if !errorlevel! equ 0 (
            set "FINAL_PYTHON=%PYTHON_PATH%"
        )
    )
)

REM 3. Ultimate failure check
if not defined FINAL_PYTHON (
    echo.
    echo ERROR: Cannot find or verify a valid '%CONDA_DEFAULT_ENV%' Conda environment.
    echo.
    echo Status from 'conda info':
    echo   Active Environment: "!ACTUAL_CONDA_ENV!" ^(Should be '%CONDA_DEFAULT_ENV%'^)
    echo.
    echo Configured path: "%PYTHON_PATH%"
    echo.
    echo Solution: Please run 'conda activate %CONDA_DEFAULT_ENV%' before running this script.
    pause
    exit /b 1
)

set "PYTHON_PATH=%FINAL_PYTHON%"
echo - Python: OK


REM Check video directory
if not exist "%VIDEO_DIR%\" (
    echo ERROR: Video directory not found
    echo Path: %VIDEO_DIR%
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Select run mode:
echo.
echo   1 - Full pipeline (dedupe + detect + cluster + Sync)
echo   2 - Skip dedupe, process faces only
echo   3 - Dedupe only
echo   4 - Dedupe report (no delete)
echo   5 - Update Video Metadata (Sync JSON)
echo   0 - Cancel
echo.
set /p MODE="Enter option [0-5]: "

if "%MODE%"=="1" goto RUN_ALL
if "%MODE%"=="2" goto RUN_NO_DEDUP
if "%MODE%"=="3" goto RUN_DEDUP_ONLY
if "%MODE%"=="4" goto RUN_DEDUP_REPORT
if "%MODE%"=="5" goto RUN_HTML_ONLY
if "%MODE%"=="0" goto CANCEL

echo Invalid option.
goto :EOF

:RUN_ALL
echo.
echo Running full pipeline...
echo ============================================
REM Force run from root dir so modules and engine imports work
pushd "%ROOT_DIR%"
echo Hash of utils.py:
certutil -hashfile utils.py MD5 | findstr /v "CertUtil"
"%PYTHON_PATH%" "tools\run.py" pipeline
popd
set "EXIT_CODE=%errorlevel%"
goto SHOW_RESULT

:RUN_NO_DEDUP
echo.
echo Skipping dedupe, processing faces...
echo ============================================
pushd "%ROOT_DIR%"
"%PYTHON_PATH%" "tools\run.py" pipeline --no-dedupe
popd
set "EXIT_CODE=%errorlevel%"
goto SHOW_RESULT

:RUN_DEDUP_ONLY
echo.
echo Running video deduplication only...
echo ============================================
pushd "%ROOT_DIR%"
"%PYTHON_PATH%" "tools\run.py" dedupe
popd
echo.
echo Dedupe complete. To remove duplicates, run:
echo   python tools\run.py dedupe --remove
goto :EOF

:RUN_DEDUP_REPORT
echo.
echo Generating deduplication report...
echo ============================================
pushd "%ROOT_DIR%"
"%PYTHON_PATH%" "tools\run.py" dedupe
popd
set "EXIT_CODE=%errorlevel%"
if exist "%ROOT_DIR%\duplicate_report.txt" (
    echo.
    echo Report saved to: duplicate_report.txt
)
goto :EOF

:RUN_HTML_ONLY
echo.
echo Updating video metadata and cache (Synchronizing JSON)...
echo ============================================
"%PYTHON_PATH%" "%ROOT_DIR%\tools\run.py" refresh
set "EXIT_CODE=%errorlevel%"
goto SHOW_RESULT

:CANCEL
echo Cancelled.
goto :EOF

:SHOW_RESULT
echo.
if "%EXIT_CODE%"=="0" (
    echo ============================================
    echo Complete!
    echo ============================================
    echo.
    echo Next steps:
    echo   1. Start the local server ^(select 'y' below^)
    echo   2. Access via http://localhost:8080/index.html
    echo   3. Update metadata ^(if needed^): Option 5 in menu
    echo.
) else (
    echo ============================================
    echo Failed!
    echo ============================================
    echo.
    echo Error code: %EXIT_CODE%
    echo.
    echo Check:
    echo   1. Video files are complete
    echo   2. Enough disk space
    echo   3. See processing.log for details
    echo.
)
goto SELECT_SERVER

:SELECT_SERVER

echo.
set /p ACTION="Start local server and open browser? (y/n): "
if /i "%ACTION%"=="y" (
    echo Starting server via web-server.cmd...
    echo ^(Close the new command window to stop the server^)
    pushd "%SCRIPT_DIR%"
    start "Video Face Index Server" cmd /c "web-server.cmd"
    popd
    timeout /t 3 >nul
    start http://localhost:8080/index.html
)

endlocal
pause
goto :EOF



