@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || goto :fail
call "%~dp0check_environment.bat" || goto :fail
echo [EEG Neurolyze] Running SIMULATED eyes-open/eyes-closed EEG.
echo This does NOT connect to Muse S Athena.
".venv\Scripts\python.exe" -m eeg_athenalyze experiment run eyes-open-closed --output "data\demo" --duration-scale 0.05 --seed 42 %*
if errorlevel 1 goto :fail
echo SUCCESS: See the new .eegz and .html files in data\demo
pause
exit /b 0
:fail
echo ERROR: Synthetic experiment did not complete.
pause
exit /b 1
