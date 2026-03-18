# Building a standalone .exe (Battery Guard Event)

Build the event-driven battery guard into a single executable so you can copy only the `.exe` (or one folder) and run it without Python or the project folder.

---

## 1. Install PyInstaller

From the project folder, with your venv activated:

```powershell
pip install -r requirements-build.txt
```

Or: `pip install pyinstaller`

---

## 2. Build

### Option A: One-folder (recommended)

Produces a folder containing the exe and support files. Copy the whole folder wherever you want.

```powershell
pyinstaller --noconsole --name battery_guard_event battery_guard_event.py
```

- **Output**: `dist\battery_guard_event\battery_guard_event.exe` (and other files in that folder).
- **Run**: Double-click the exe or run it from a shortcut. Log file `battery_guard_event.log` is created in the **same folder as the exe** (or set "Start in" in Task Scheduler to that folder).

### Option B: One-file (single .exe)

Produces one self-contained exe. Slightly slower first start (unpacks to temp).

```powershell
pyinstaller --noconsole --onefile --name battery_guard_event battery_guard_event.py
```

- **Output**: `dist\battery_guard_event.exe`.
- **Run**: Copy that exe anywhere. Log file is created in the **current working directory** when the exe runs, so in Task Scheduler / shortcut set **Start in** to the folder where you want the log (e.g. `C:\BatteryGuard` or next to the exe).

---

## 3. Run on startup with the .exe

- **Task Scheduler**  
  - **Program/script**: path to `battery_guard_event.exe` (e.g. `C:\Tools\battery_guard_event.exe` or `C:\Tools\battery_guard_event\battery_guard_event.exe`).  
  - **Start in**: same folder as the exe (or a dedicated folder for logs if you prefer).

- **Startup shortcut**  
  - **Target**: path to the exe.  
  - **Start in**: same folder as the exe so the log is written there.

No batch file or Python/venv needed; point directly at the exe.

---

## 4. Optional: batch wrapper

If you want a small launcher that always sets the working directory to the exe's folder (e.g. for one-file exe when run from a shortcut that doesn't set "Start in"),

1. Copy `run_battery_guard_event_exe.bat` from the repo into the **same folder** as `battery_guard_event.exe`.
2. Use the **batch** as the Task Scheduler / Startup target instead of the exe.

The batch runs the exe and sets "Start in" to that folder so the log is created there.

---

## Notes

- **Antivirus**: One-file builds sometimes trigger warnings (unpacking to temp). One-folder build usually doesn't.
- **Updates**: After changing `battery_guard_event.py`, run the same `pyinstaller` command again and replace the old exe (or folder) with the new build.
- **Logs**: Rotating log, max ~4 MB, same as the Python script.
