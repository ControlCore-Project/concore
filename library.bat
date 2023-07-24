@echo off
if "%2" == "" (
  if exist "..\tools\%1" (
    if exist "%1" (
      echo "cannot create library link over existing file"
    ) else (
      echo "mklink %1 ..\tools\%1"
      mklink "%1" "..\tools\%1"
    )
  ) else (
    echo "..\tools\%1 does not exist"
  )
) else (
  if exist "%1\%2" (
    if exist "%2" (
      echo "cannot create library link over existing file"
    ) else (
      echo "mklink %2 %1\%2"
      mklink "%2" "%1\%2"
    )
  ) else (
    echo "%1\%2 does not exist"
  )
)
  
