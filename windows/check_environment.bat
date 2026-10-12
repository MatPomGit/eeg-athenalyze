@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Run windows\setup_environment.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" -c "import sys, eeg_athenalyze; assert sys.version_info[:2] == (3, 12); print('EEG Neurolyze environment OK')"
exit /b %errorlevel%
