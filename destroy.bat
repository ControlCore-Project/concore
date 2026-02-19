@echo off

if not exist "%1" (
    echo "%1 does not exist"
    exit /b 1
)

if not exist "%1\stop.bat" (
    echo "%1 is not a concore study"
    exit /b 1
)

echo Stopping study...
call "%1\stop.bat"

if exist "%1\clear.bat" (
    echo Clearing study...
    call "%1\clear.bat"
)

echo Removing study directory...
rmdir /s /q "%1"

echo Done.

