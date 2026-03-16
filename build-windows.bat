@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE="

if exist "%LocalAppData%\Python\bin\python.exe" set "PYTHON_EXE=%LocalAppData%\Python\bin\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"

if not defined PYTHON_EXE (
  where py >nul 2>nul && set "PYTHON_EXE=py -3"
)

if not defined PYTHON_EXE (
  where python >nul 2>nul && set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
  echo Python was not found.
  pause
  exit /b 1
)

call %PYTHON_EXE% -m pip install -r app\requirements.txt pyinstaller
if errorlevel 1 (
  echo Failed to install build requirements.
  pause
  exit /b 1
)

call %PYTHON_EXE% -m PyInstaller --noconfirm build.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo Windows standalone build created in dist\
pause
