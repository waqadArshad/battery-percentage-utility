@echo off
rem Run the built battery_guard_event.exe from this folder (no console).
rem Copy this batch next to battery_guard_event.exe and use it as the
rem Task Scheduler / Startup target so the log is created in this folder.
cd /d "%~dp0"
"%~dp0battery_guard_event.exe"
