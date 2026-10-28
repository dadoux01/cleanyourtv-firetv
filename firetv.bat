@echo off
rem Thin wrapper: the logic lives in firetv.py. / Enveloppe : la logique est dans firetv.py.
rem Usage: firetv.bat --host 192.168.1.50 probe
cd /d "%~dp0"
where py >nul 2>nul && (py -3 firetv.py %* & exit /b %errorlevel%)
where python >nul 2>nul && (python firetv.py %* & exit /b %errorlevel%)
echo Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/
exit /b 1
