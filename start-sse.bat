@echo off
cd /d "%~dp0"
uv run python run.py -t sse --host 0.0.0.0 -p 8000
pause
