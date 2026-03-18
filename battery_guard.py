import logging
from logging.handlers import RotatingFileHandler
import time
import time as _time  # for monotonic timing

import psutil
from winotify import Notification, audio

LOW_THRESHOLD = 30   # percent
HIGH_THRESHOLD = 90  # percent
CHECK_INTERVAL_SECONDS = 60
MIN_NOTIFICATION_GAP_SECONDS = 300  # minimum seconds between same-type notifications


def setup_logging() -> None:
    file_handler = RotatingFileHandler(
        "battery_guard.log",
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
    )


def get_battery_info():
    battery = psutil.sensors_battery()
    if battery is None:
        return None, None
    return battery.percent, battery.power_plugged


def main():
    setup_logging()
    logging.info(
        "Starting battery_guard with LOW_THRESHOLD=%s%%, HIGH_THRESHOLD=%s%%, "
        "CHECK_INTERVAL_SECONDS=%s",
        LOW_THRESHOLD,
        HIGH_THRESHOLD,
        CHECK_INTERVAL_SECONDS,
    )

    low_notified = False
    high_notified = False
    last_low_notification_time = 0.0
    last_high_notification_time = 0.0

    logging.info("battery_guard main loop starting.")

    try:
        while True:
            percent, plugged = get_battery_info()
            if percent is None:
                logging.warning("No battery detected; sleeping for %s seconds", CHECK_INTERVAL_SECONDS)
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

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
                    high_notified = False  # reset opposite side
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
                    low_notified = False  # reset opposite side
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

            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("battery_guard interrupted by user (KeyboardInterrupt). Exiting.")


if __name__ == "__main__":
    main()