cd fri\server
python main.py
if errorlevel 1 (
    echo.
    echo Error: Make sure modules are installed from fri/requirements.txt
    echo Run: pip install -r fri/requirements.txt
    echo.
)