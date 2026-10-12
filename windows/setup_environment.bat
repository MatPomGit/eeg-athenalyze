@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || goto :fail
echo [EEG Neurolyze] Preparing isolated Python 3.12 environment...
where py >nul 2>nul || (echo ERROR: Windows Python launcher not found. Install Python 3.12. & goto :fail)
py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)" || goto :fail
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv ".venv" || goto :fail
)
".venv\Scripts\python.exe" -m pip install . || goto :fail
".venv\Scripts\python.exe" -c "import eeg_athenalyze; print('Environment OK')" || goto :fail
".venv\Scripts\python.exe" -m eeg_athenalyze --help || goto :fail
echo SUCCESS: The project is installed in "%ROOT%\.venv"
exit /b 0
:fail
echo ERROR: Setup failed. No recordings were modified.
pause
exit /b 1
