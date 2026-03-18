# Run Battery Guard on Windows Startup

Use the **event-driven** script (`battery_guard_event.py`) so it runs in the background with no console window.

**Pick one** of the two options below (Task Scheduler or Startup folder)—you don’t need both.

Use **your actual project folder** wherever you see `<project-folder>` (e.g. `C:\Projects\battery-percentage-utility` or `D:\Tools\battery-guard`).

---

## Option 1: Task Scheduler (recommended)

1. Open **Task Scheduler** (search in Start or `taskschd.msc`).
2. **Create Task** (not “Create Basic Task”):
   - **General**: Name e.g. `Battery Guard`, optionally “Run whether user is logged on or not” **unchecked** so it runs as you.
   - **Triggers**: New → **At log on** → your user account → OK.
   - **Actions**: New → **Start a program**:
     - **Program/script**:  
       `<project-folder>\run_battery_guard_event.bat`
     - **Start in**:  
       `<project-folder>`
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
     `<project-folder>\run_battery_guard_event.bat`
   - **Start in**:  
     `<project-folder>`
   - Name it e.g. `Battery Guard`.
3. After next logon, the guard runs in the background (no window).

---

## Using the built .exe instead

If you built a standalone .exe (see **BUILD.md**), use the **same** Task Scheduler or Startup folder approach, but point at the exe instead of the batch:

| Step | Python + batch | Built .exe |
|------|----------------|------------|
| **Task Scheduler – Program/script** | `<project-folder>\run_battery_guard_event.bat` | Path to `battery_guard_event.exe` (e.g. `C:\Tools\battery_guard_event.exe` for one-file, or `C:\Tools\battery_guard_event\battery_guard_event.exe` for one-folder) |
| **Task Scheduler – Start in** | `<project-folder>` | The **folder that contains the exe** (so the log is created there) |
| **Startup shortcut – Target** | `<project-folder>\run_battery_guard_event.bat` | Path to `battery_guard_event.exe` |
| **Startup shortcut – Start in** | `<project-folder>` | The folder that contains the exe |

- No Python or project folder needed; copy only the exe (or the one-folder `dist\battery_guard_event\` output) to any location.
- **Optional**: Copy `run_battery_guard_event_exe.bat` from the repo into the **same folder** as the exe, and use that batch as the Task Scheduler / Startup target instead of the exe; the batch sets “Start in” to that folder so the log is always written there.

---

## Moving the project to a different folder

- **No file changes needed** in the repo. All paths inside the project are relative:
  - `run_battery_guard_event.bat` uses `%~dp0` (the folder the batch lives in), so it works from any location.
  - Log files (`battery_guard_event.log`, `battery_guard.log`) are created in the project folder when the batch runs (it sets the working directory to that folder).
- **If you already set up startup**: update the path in Task Scheduler or in your Startup shortcut to the new project folder (Program/script and Start in, or shortcut Target and Start in). Or delete the old task/shortcut and create a new one using the new `<project-folder>`.

---

## Stopping it

- **Task Scheduler**: Open Task Scheduler → find “Battery Guard” → End Task, or disable the task.
- **Startup shortcut**: Open Task Manager → find `pythonw.exe` (Python) or `battery_guard_event.exe` (built exe) → End task.

Logs are in `battery_guard_event.log` in the folder where the app runs (project folder or exe folder; rotating, max ~4 MB).
