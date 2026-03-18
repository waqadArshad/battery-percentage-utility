"""
Event-driven battery guard using Windows power setting notifications.
Same behavior as battery_guard.py (thresholds, hysteresis, notifications)
but reacts to battery % and AC/DC change events instead of polling.

Windows-only; requires no polling loop.
"""
from __future__ import annotations

import ctypes
import logging
import sys
import time as _time
from ctypes import wintypes
from typing import Any, Callable, Optional

if sys.platform != "win32":
    raise SystemExit("battery_guard_event is Windows-only.")

from logging.handlers import RotatingFileHandler

import psutil
from winotify import Notification, audio

# --- Same config as battery_guard.py ---
LOW_THRESHOLD = 30   # percent
HIGH_THRESHOLD = 90  # percent
MIN_NOTIFICATION_GAP_SECONDS = 300  # minimum seconds between same-type notifications


def setup_logging(log_file: str = "battery_guard_event.log") -> None:
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler(),
        ],
        force=True,
    )


def get_battery_info() -> tuple[Optional[int], Optional[bool]]:
    battery = psutil.sensors_battery()
    if battery is None:
        return None, None
    return battery.percent, battery.power_plugged


def check_and_notify(
    percent: Optional[int],
    plugged: Optional[bool],
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Run threshold/hysteresis/notification logic once.
    Same logic as battery_guard.py main loop body.
    Returns updated state dict.
    """
    low_notified = state.get("low_notified", False)
    high_notified = state.get("high_notified", False)
    last_low_notification_time = state.get("last_low_notification_time", 0.0)
    last_high_notification_time = state.get("last_high_notification_time", 0.0)

    if percent is None or plugged is None:
        logging.warning("No battery info; skipping check.")
        return state

    logging.info(
        "Battery status: %s%%, plugged=%s, low_notified=%s, high_notified=%s",
        percent,
        plugged,
        low_notified,
        high_notified,
    )

    now = _time.monotonic()

    # Low battery and not plugged in
    if not plugged and percent <= LOW_THRESHOLD:
        if (
            not low_notified
            and now - last_low_notification_time >= MIN_NOTIFICATION_GAP_SECONDS
        ):
            logging.info("Low threshold reached (%s%%). Prompting to connect charger.", percent)
            message = f"Battery at {percent}%. Please connect the charger."
            print(message)
            toast = Notification(
                app_id="Battery Guard",
                title="Battery Guard",
                msg=message,
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            low_notified = True
            high_notified = False
            last_low_notification_time = now

    # High battery and plugged in
    if plugged and percent >= HIGH_THRESHOLD:
        if (
            not high_notified
            and now - last_high_notification_time >= MIN_NOTIFICATION_GAP_SECONDS
        ):
            logging.info("High threshold reached (%s%%). Prompting to disconnect charger.", percent)
            message = f"Battery at {percent}%. Please disconnect the charger."
            print(message)
            toast = Notification(
                app_id="Battery Guard",
                title="Battery Guard",
                msg=message,
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            high_notified = True
            low_notified = False
            last_high_notification_time = now

    # Reset notifications when we move away from thresholds
    if percent > LOW_THRESHOLD + 5 and low_notified:
        logging.info(
            "Battery moved above low reset band (%s%% > %s%%). Clearing low_notified.",
            percent,
            LOW_THRESHOLD + 5,
        )
        low_notified = False
    if percent < HIGH_THRESHOLD - 5 and high_notified:
        logging.info(
            "Battery moved below high reset band (%s%% < %s%%). Clearing high_notified.",
            percent,
            HIGH_THRESHOLD - 5,
        )
        high_notified = False

    return {
        "low_notified": low_notified,
        "high_notified": high_notified,
        "last_low_notification_time": last_low_notification_time,
        "last_high_notification_time": last_high_notification_time,
    }


# --- Win32 power event listener (ctypes) ---
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_POWERBROADCAST = 0x0218
PBT_POWERSETTINGCHANGE = 0x8013
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
DEVICE_NOTIFY_WINDOW_HANDLE = 0x00000000
HWND_MESSAGE = wintypes.HWND(-3)
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1
GWLP_USERDATA = -21

WNDCLASS_NAME = "BatteryGuardEventWindow"


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


def make_guid(data1: int, data2: int, data3: int, d4: tuple[int, ...]) -> GUID:
    g = GUID()
    g.Data1 = data1
    g.Data2 = data2
    g.Data3 = data3
    g.Data4[:] = (wintypes.BYTE * 8)(*d4)
    return g


GUID_BATTERY_PERCENTAGE_REMAINING = make_guid(
    0xA7AD8041, 0xB45A, 0x4CAE,
    (0x87, 0xA3, 0xEE, 0xCB, 0xB4, 0x68, 0xA9, 0xE1),
)
GUID_ACDC_POWER_SOURCE = make_guid(
    0x5D3E9A59, 0xE9D5, 0x4B00,
    (0xA6, 0xBD, 0xFF, 0x34, 0xFF, 0x51, 0x65, 0x48),
)


class POWERBROADCAST_SETTING(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", GUID),
        ("DataLength", wintypes.DWORD),
        ("Data", wintypes.BYTE * 1),
    ]


LRESULT = wintypes.LPARAM
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)
HICON = getattr(wintypes, "HICON", wintypes.HANDLE)
HBRUSH = getattr(wintypes, "HBRUSH", wintypes.HANDLE)
HMENU = getattr(wintypes, "HMENU", wintypes.HANDLE)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", HICON),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


HPOWERNOTIFY = wintypes.HANDLE

# Prototypes
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT

user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int

user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT

user32.RegisterPowerSettingNotification.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(GUID), wintypes.DWORD
]
user32.RegisterPowerSettingNotification.restype = HPOWERNOTIFY

user32.UnregisterPowerSettingNotification.argtypes = [HPOWERNOTIFY]
user32.UnregisterPowerSettingNotification.restype = wintypes.BOOL

user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LPARAM]
user32.SetWindowLongPtrW.restype = wintypes.LPARAM
user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = wintypes.LPARAM

PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
kernel32.SetConsoleCtrlHandler.argtypes = [PHANDLER_ROUTINE, wintypes.BOOL]
kernel32.SetConsoleCtrlHandler.restype = wintypes.BOOL


class PowerEventListener:
    """
    Hidden message-only window that subscribes to battery % and AC/DC power
    setting changes. On each event (and once on startup), runs the guard logic.
    """

    def __init__(self, on_power_event: Callable[[], None]) -> None:
        self._on_power_event = on_power_event
        self._self_pyobj = ctypes.py_object(self)
        self.hInstance = kernel32.GetModuleHandleW(None)
        self.hwnd = wintypes.HWND(0)
        self._wndproc = WNDPROC(self._wndproc_thunk)
        self._ctrl_handler = PHANDLER_ROUTINE(self._ctrl_thunk)
        self._h_notifies: list[HPOWERNOTIFY] = []

    def _wndproc_thunk(self, hwnd: wintypes.HWND, msg: int, wParam: wintypes.WPARAM, lParam: wintypes.LPARAM) -> LRESULT:
        ptr = user32.GetWindowLongPtrW(hwnd, GWLP_USERDATA)
        if ptr:
            obj = ctypes.cast(ptr, ctypes.POINTER(ctypes.py_object)).contents.value
        else:
            obj = self

        if msg == WM_POWERBROADCAST and wParam == PBT_POWERSETTINGCHANGE and lParam:
            pbs = ctypes.cast(lParam, ctypes.POINTER(POWERBROADCAST_SETTING)).contents
            if pbs.DataLength >= ctypes.sizeof(wintypes.DWORD):
                data_offset = ctypes.sizeof(GUID) + ctypes.sizeof(wintypes.DWORD)
                data_addr = ctypes.addressof(pbs) + data_offset
                value = int(wintypes.DWORD.from_address(data_addr).value)
                if bytes(pbs.PowerSetting) == bytes(GUID_BATTERY_PERCENTAGE_REMAINING):
                    logging.debug("Battery percent event: %s%%", value)
                if bytes(pbs.PowerSetting) == bytes(GUID_ACDC_POWER_SOURCE):
                    logging.debug("AC/DC power source event: %s", value)
                try:
                    obj._on_power_event()
                except Exception as e:
                    logging.exception("Error in power event callback: %s", e)
            return 1

        if msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

    def _ctrl_thunk(self, ctrl_type: int) -> bool:
        if ctrl_type in (CTRL_C_EVENT, CTRL_BREAK_EVENT):
            if self.hwnd:
                user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            return True
        return False

    def _register_class(self) -> None:
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = 0
        wc.lpfnWndProc = self._wndproc
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = self.hInstance
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = WNDCLASS_NAME
        wc.hIconSm = None
        if not user32.RegisterClassExW(ctypes.byref(wc)):
            raise ctypes.WinError(ctypes.get_last_error())

    def _create_window(self) -> None:
        hwnd = user32.CreateWindowExW(
            0, WNDCLASS_NAME, "",
            0, 0, 0, 0, 0,
            HWND_MESSAGE, None, self.hInstance, None,
        )
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        self.hwnd = hwnd
        self_ptr = ctypes.addressof(self._self_pyobj)
        user32.SetWindowLongPtrW(self.hwnd, GWLP_USERDATA, wintypes.LPARAM(self_ptr))

    def _register_notifications(self) -> None:
        for guid in (GUID_BATTERY_PERCENTAGE_REMAINING, GUID_ACDC_POWER_SOURCE):
            h = user32.RegisterPowerSettingNotification(
                self.hwnd, ctypes.byref(guid), DEVICE_NOTIFY_WINDOW_HANDLE
            )
            if not h:
                raise ctypes.WinError(ctypes.get_last_error())
            self._h_notifies.append(h)

    def _message_loop(self) -> None:
        msg = MSG()
        while True:
            r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r == 0:
                break
            if r == -1:
                raise ctypes.WinError(ctypes.get_last_error())
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _cleanup(self) -> None:
        if getattr(self, "_ctrl_handler", None):
            kernel32.SetConsoleCtrlHandler(self._ctrl_handler, False)
        for h in getattr(self, "_h_notifies", []):
            if h:
                user32.UnregisterPowerSettingNotification(h)
        self._h_notifies.clear()
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = wintypes.HWND(0)
        if self.hInstance:
            user32.UnregisterClassW(WNDCLASS_NAME, self.hInstance)

    def run(self) -> int:
        self._register_class()
        try:
            self._create_window()
            if not kernel32.SetConsoleCtrlHandler(self._ctrl_handler, True):
                raise ctypes.WinError(ctypes.get_last_error())
            self._register_notifications()
            # Initial check (same as polling version's first iteration)
            self._on_power_event()
            self._message_loop()
            return 0
        finally:
            self._cleanup()


def main() -> None:
    setup_logging()
    logging.info(
        "Starting battery_guard_event (event-driven) LOW_THRESHOLD=%s%%, HIGH_THRESHOLD=%s%%, "
        "MIN_NOTIFICATION_GAP_SECONDS=%s",
        LOW_THRESHOLD,
        HIGH_THRESHOLD,
        MIN_NOTIFICATION_GAP_SECONDS,
    )

    state: dict[str, Any] = {}

    def on_power_event() -> None:
        nonlocal state
        percent, plugged = get_battery_info()
        state = check_and_notify(percent, plugged, state)

    listener = PowerEventListener(on_power_event)
    try:
        listener.run()
    except KeyboardInterrupt:
        pass
    logging.info("battery_guard_event exiting.")


if __name__ == "__main__":
    main()
