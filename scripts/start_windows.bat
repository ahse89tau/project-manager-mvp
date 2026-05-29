@echo off
setlocal

cd /d %~dp0\..
echo Starting pm-app container...
docker compose up -d --build
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
echo pm-app is running at http://localhost:8000

endlocal
