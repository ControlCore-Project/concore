@echo off
if exist "%1\stop.bat" (rmdir /s/q %1) else (echo "%1 is not a concore study")

