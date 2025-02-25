@echo off
setlocal EnableDelayedExpansion

:: Extracting parameters safely
set "file1=%~f1"
set "file2=%~2"
set "dir1=%~dp1"
set "name1=%~n1"
set "ext1=%~x1"

:: Handling spaces in paths by ensuring the format remains intact
set "file1=!file1:\=\\!"
set "dir1=!dir1:\=\\!"

:: If the second argument (file2) is not provided
if not defined file2 (
    if /I "%ext1%"==".graphml" (
        echo python mkconcore.py "!file1!" "!dir1!" "!name1!" windows
        python mkconcore.py "!file1!" "!dir1!" "!name1!" windows
    ) else (
        echo python mkconcore.py "!dir1!!name1!.graphml" "!dir1!" "!name1!" windows
        python mkconcore.py "!dir1!!name1!.graphml" "!dir1!" "!name1!" windows
    )
) else (
    if /I "%ext1%"==".graphml" (
        echo python mkconcore.py "!file1!" "!dir1!" "!file2!" windows
        python mkconcore.py "!file1!" "!dir1!" "!file2!" windows
    ) else (
        echo python mkconcore.py "!dir1!!name1!.graphml" "!dir1!" "!file2!" windows
        python mkconcore.py "!dir1!!name1!.graphml" "!dir1!" "!file2!" windows
    )
)

endlocal
