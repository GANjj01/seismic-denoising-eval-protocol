@echo off
setlocal
set ROOT=%~dp0..
if "%CONDA_BAT%"=="" (
  echo Set CONDA_BAT to your conda activate.bat path, or run:
  echo python "%ROOT%\scripts\run_smoke_test.py"
  exit /b 2
)
call "%CONDA_BAT%" seismic
python "%ROOT%\scripts\run_smoke_test.py"
