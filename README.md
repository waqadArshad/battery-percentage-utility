# Battery Percentage Utility

Windows tray-style notifications when your laptop battery is low or fully charged. Helps avoid deep discharge and overcharging by reminding you to plug in or unplug.

---

## Features

- **Low battery alert** — Notifies when battery falls below a threshold (default 30%).
- **High battery alert** — Notifies when battery reaches a high level while plugged in (default 90%), so you can unplug to avoid keeping it at 100%.
- **Hysteresis** — Won’t re-notify for the same condition until you’ve crossed the threshold and come back (and a minimum time has passed).
- **Event-driven (recommended)** — `battery_guard_event.py` uses Windows power notifications; no polling, no busy loop.
- **Polling option** — `battery_guard.py` uses a simple interval loop if you prefer or need it.
- **No console window** — Run via `pythonw` or the included batch file for a silent background process.
- **Standalone .exe** — Build with PyInstaller and run without Python installed.

---

## Requirements

- **Windows** (the event-driven script is Windows-only; the polling script could be adapted for other OSes).
- **Python 3.8+**
- **Dependencies**: `psutil`, `winotify` (see [requirements.txt](requirements.txt)).

---

## Quick start

### 1. Clone and set up

```powershell
git clone https://github.com/waqadArshad/battery-percentage-utility.git
cd battery-percentage-utility
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run once (event-driven, recommended)

```powershell
python battery_guard_event.py
```

Or run in the background with no console window:

```powershell
.\run_battery_guard_event.bat
```

The batch file uses `venv\Scripts\pythonw.exe` if present, otherwise `pythonw` from PATH.

### 3. Run on startup

To have the guard start automatically at logon, use **Task Scheduler** or the **Startup folder**. Step-by-step instructions:

- **[Run on startup (docs/RUN_ON_STARTUP.md)](docs/RUN_ON_STARTUP.md)** — Task Scheduler and Startup folder, plus how to use the built .exe.

### 4. Build a standalone .exe (optional)

To run without Python installed, build an executable with PyInstaller:

- **[Building the .exe (docs/BUILD.md)](docs/BUILD.md)** — One-folder and one-file builds, and how to run the exe on startup.

---

## Scripts

| Script | Description |
|--------|-------------|
| **battery_guard_event.py** | Event-driven; subscribes to Windows power events. **Recommended** for normal use. |
| **battery_guard.py** | Polling-based; checks battery every 60 seconds. Use if the event-driven version doesn’t fit your setup. |

Both use the same thresholds and notification logic; only the way they detect changes differs.

---

## Configuration

Edit the script you use:

- **LOW_THRESHOLD** — Notify when battery drops below this (default `30` %).
- **HIGH_THRESHOLD** — Notify when battery reaches this while plugged in (default `90` %).
- **MIN_NOTIFICATION_GAP_SECONDS** — Minimum seconds between repeated same-type notifications (default `300`).

In `battery_guard.py` you can also set **CHECK_INTERVAL_SECONDS** (default `60`).

---

## Logs

- **battery_guard_event.py** → `battery_guard_event.log`
- **battery_guard.py** → `battery_guard.log`

Logs are rotating (max ~1 MB per file, 3 backups, ~4 MB total). They are created in the current working directory (project folder when using the batch, or the folder set as “Start in” in Task Scheduler).

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/RUN_ON_STARTUP.md](docs/RUN_ON_STARTUP.md) | Run at logon via Task Scheduler or Startup folder; using the built .exe; moving the project; stopping. |
| [docs/BUILD.md](docs/BUILD.md) | Build a standalone .exe with PyInstaller (one-folder or one-file). |

---

## License

See [LICENSE](LICENSE) if present; otherwise use at your own discretion.
