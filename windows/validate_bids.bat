@echo off
setlocal
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1
call "%~dp0check_environment.bat" || exit /b 1
".venv\Scripts\python.exe" -m eeg_athenalyze bids validate %*
exit /b %errorlevel%
