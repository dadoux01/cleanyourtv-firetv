@echo off
rem Thin wrapper: the logic lives in firetv.py. / Enveloppe : la logique est dans firetv.py.
rem Usage: firetv.bat --host 192.168.1.50 probe   (paths you pass are read from the current folder)
setlocal
set "HERE=%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 goto use_python
echo Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/ 1>&2
exit /b 1
:use_py
py -3 "%HERE%firetv.py" %*
exit /b
:use_python
python "%HERE%firetv.py" %*
exit /b
