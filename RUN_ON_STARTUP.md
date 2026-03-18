# Run Battery Guard on Windows Startup

Use the **event-driven** script (`battery_guard_event.py`) so it runs in the background with no console window. Two ways to start it at login:

---

## Option 1: Task Scheduler (recommended)

1. Open **Task Scheduler** (search in Start or `taskschd.msc`).
2. **Create Task** (not “Create Basic Task”):
   - **General**: Name e.g. `Battery Guard`, optionally “Run whether user is logged on or not” **unchecked** so it runs as you.
   - **Triggers**: New → **At log on** → your user account → OK.
   - **Actions**: New → **Start a program**:
     - **Program/script**:  
       `C:\GitHub-Repos\Waqad\battery-percentage-utility\run_battery_guard_event.bat`
     - **Start in**:  
       `C:\GitHub-Repos\Waqad\battery-percentage-utility`
   - **Conditions**: Uncheck “Start only when on AC power” if you want it on battery too.
   - **Settings**: Optional “Allow task to be run on demand”.
3. Click **OK**. Test with **Run** from Task Scheduler.

The batch uses `pythonw` so no console window appears. Log file: `battery_guard_event.log` in the project folder.

---

## Option 2: Startup folder

1. Open your **Startup** folder:
   - Press `Win + R`, type `shell:startup`, Enter.
2. Create a **shortcut**:
   - Right‑click → New → Shortcut.
   - **Target**:  
     `C:\GitHub-Repos\Waqad\battery-percentage-utility\run_battery_guard_event.bat`
   - **Start in**:  
     `C:\GitHub-Repos\Waqad\battery-percentage-utility`
   - Name it e.g. `Battery Guard`.
3. After next logon, the guard runs in the background (no window).

---

## Stopping it

- **Task Scheduler**: Open Task Scheduler → find “Battery Guard” → End Task, or disable the task.
- **Startup shortcut**: Open Task Manager → find `pythonw.exe` (or the batch) → End task.

Logs are in `battery_guard_event.log` in the project folder (rotating, max ~4 MB).
