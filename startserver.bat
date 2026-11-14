cd fri\server
rem main.py refuses to start without a secret key; use a throwaway one for local runs
if not defined FLASK_SECRET_KEY for /f %%k in ('python -c "import secrets; print(secrets.token_hex(32))"') do @set "FLASK_SECRET_KEY=%%k"
python main.py
if errorlevel 1 (
    echo.
    echo Error: the server exited with an error ^(see above^). If a module is missing:
    echo Run: pip install -r fri/requirements.txt
    echo.
)