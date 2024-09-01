import cv2
import gspread
import numpy as np
from datetime import datetime
from resources.scripts.FileIO import read
from resources.scripts.Sheets import update, pull_statuses
from resources.scripts.Logging import write_log
from resources.scripts.TermColor import TermColor
from gspread import Cell, Worksheet, service_account
from resources.scripts.QRProcessor import QRProcessor
from resources.scripts.Exceptions import BadOrderException, UnknownQRCodeException


if __name__ == "__main__":
    tc: TermColor = TermColor()
    tc.print_ok("Setting up")

    # variables
    entry: dict[str, str] = {}
    devices: dict[str, Cell] = {}

    # file i/o and images
    decrypt: dict[str, str] = read("resources/data/validation.json")
    settings: dict[str, str] = read("resources/data/settings.json")
    updating: np.ndarray = cv2.imread("resources/img/updating.png")

    # gspread setup
    client: service_account = gspread.service_account_from_dict(
        read("resources/data/api_key.json")
    )

    sheets: dict[str, Worksheet] = {
        "chromebook": client.open("Chromebook Tracker").worksheet(settings["chromebook sheet"]),
        "calculator": client.open("Chromebook Tracker").worksheet(settings["calculator sheet"]),
        "religion": client.open("Chromebook Tracker").worksheet(settings["religion sheet"]),
        "science": client.open("Chromebook Tracker").worksheet(settings["science sheet"])
    }

    # Update statuses of all rentals
    for s in sheets.values():
        devices.update(pull_statuses(s))

    # cv2
    qr_proc: QRProcessor = QRProcessor(decrypt)

    while True:
        try:
            device: str
            action: str
            student: str
            entry: dict[str, str]

            device, action = qr_proc.process_code(
                qr_proc.read_code("Show Rental", [*devices]),
                devices,
                "device"
            )

            student = qr_proc.process_code(
                qr_proc.read_code("Show ID", [*devices]),
                devices,
                "student"
            )

            cv2.waitKey(500)
            cv2.imshow("Scanner", updating)
            cv2.waitKey(1)

            # Perform the update
            current_time: datetime = datetime.now()
            entry["action"] = action
            entry["device"] = device
            entry["date"] = f"{current_time.day}/{current_time.month}/{current_time.year}"
            entry["student"] = student
            entry["time"] = f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}"

            if "CALC" in device:
                update(entry, sheets["calculator"])
            elif "REL" in device:
                update(entry, sheets["religion"])
            elif "SCI" in device:
                update(entry, sheets["science"])
            else:
                update(entry, sheets["chromebook"])

            # Update dicts in charge of keeping track of whether a device is rented out or not
            for s in sheets.values():
                devices.update(pull_statuses(s))

        # cv2 throws random errors when it thinks it detects a qr code
        # Catch all of these errors and simply put warning
        except cv2.error:
            tc.print_warning("OpenCV threw some errors, can likely ignore")

        except BadOrderException:
            continue

        except UnknownQRCodeException:
            continue

        # Catch all other errors and write traceback to log file
        except (Exception,):
            cv2.destroyAllWindows()
            tc.print_fatal("Unknown error occurred. See logs for more details")
            write_log()
