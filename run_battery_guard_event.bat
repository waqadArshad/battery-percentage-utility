@echo off
rem Run event-driven battery guard with no console window (pythonw).
rem Use this from Task Scheduler or a Startup folder shortcut.
cd /d "%~dp0"

if exist "%~dp0venv\Scripts\pythonw.exe" (
    "%~dp0venv\Scripts\pythonw.exe" "%~dp0battery_guard_event.py"
) else (
    pythonw "%~dp0battery_guard_event.py"
)
