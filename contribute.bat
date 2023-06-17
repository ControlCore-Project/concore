@echo off

REM Check if the first 3 arguments are provided
if "%~1" == "" goto :missing_arg
if "%~2" == "" goto :missing_arg
if "%~3" == "" goto :missing_arg

REM Check and set default values for the last three arguments if not provided
if "%~4"=="" (set arg4="#") else (set arg4=%~4)
if "%~5"=="" (set arg5="#") else (set arg5=%~5)
if "%~6"=="" (set arg6="#") else (set arg6=%~6)
python contribute.py %1 %2 %3 %arg4% %arg5% %arg6%
goto :eof

:missing_arg
echo "Error: The first 3 arguments are mandatory."
echo "Usage: ./contribute.bat <Study-Name> <Full-Path-To-Study> <Author-Name> <Branch-Name> <PR-title> <PR-Body>"



