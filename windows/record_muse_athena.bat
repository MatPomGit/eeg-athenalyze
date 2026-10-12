@echo off
setlocal
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1
call "%~dp0check_environment.bat" || exit /b 1
echo WARNING: Real Muse S Athena acquisition. No synthetic fallback.
".venv\Scripts\python.exe" -m eeg_athenalyze record --device muse-athena %*
set "CODE=%errorlevel%"
if not "%CODE%"=="0" echo Acquisition failed. No simulated data were substituted.
pause
exit /b %CODE%
