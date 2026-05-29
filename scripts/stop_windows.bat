@echo off
setlocal

cd /d %~dp0\..
echo Stopping pm-app container...
docker compose down
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
echo pm-app is stopped.

endlocal
