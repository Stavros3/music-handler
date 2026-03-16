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
  echo Please install Python 3 and try again.
  pause
  exit /b 1
)

call %PYTHON_EXE% -c "import PySide6, send2trash" >nul 2>nul
if errorlevel 1 (
  echo Installing required Python packages...
  call %PYTHON_EXE% -m pip install -r "app\requirements.txt"
  if errorlevel 1 (
    echo Failed to install required packages.
    pause
    exit /b 1
  )
)

call %PYTHON_EXE% "app\app.py"
if errorlevel 1 (
  echo The application closed with an error.
  pause
  exit /b 1
)
