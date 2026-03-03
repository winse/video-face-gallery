@echo off
setlocal

for %%i in ("%~dp0.") do set "SCRIPT_DIR=%%~fi"

pushd "%SCRIPT_DIR%\.."
python tools\run.py serve --host 0.0.0.0 --port 8080 --directory web
popd

endlocal


