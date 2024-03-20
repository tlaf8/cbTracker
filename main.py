import cv2
import gspread
import numpy as np
from datetime import datetime
from resources.scripts.FileIO import read
from resources.scripts.Sheets import update
from resources.scripts.Logging import write_log
from resources.scripts.TermColor import TermColor
from resources.scripts.QRProcessor import QRProcessor
from resources.scripts.Exceptions import BadOrderException, UnknownQRCodeException


if __name__ == "__main__":
    tc: TermColor = TermColor()
    tc.print_ok("Setting things up")

    # variables
    entry: dict[str, str] = {}
    devices: dict[str, str] = {}

    # file i/o and images
    decrypt: dict[str, str] = read("resources/data/validation.json")
    settings: dict[str, str] = read("resources/data/settings.json")
    updating: np.ndarray = cv2.imread("resources/img/updating.png")

    # gspread setup
    client: gspread.service_account = gspread.service_account_from_dict(
        read("resources/data/api_key.json")
    )
    cb_sheet: gspread.Worksheet = client.open("Chromebook Tracker").worksheet(settings["chromebook sheet"])
    calc_sheet: gspread.Worksheet = client.open("Chromebook Tracker").worksheet(settings["calculator sheet"])

    # gspread reading
    lr_cb: int = len(cb_sheet.col_values(7))
    lr_calc: int = len(calc_sheet.col_values(7))

    devices.update(
        zip(
            [name.value for name in cb_sheet.range(f"G2:G{lr_cb}")],
            cb_sheet.range(f"H2:H{lr_cb}")
        )
    )

    devices.update(
        zip(
            [name.value for name in calc_sheet.range(f"G2:G{lr_calc}")],
            calc_sheet.range(f"H2:H{lr_calc}")
        )
    )

    # cv2
    qr_proc: QRProcessor = QRProcessor(decrypt, devices)

    while True:
        try:
            device: str
            action: str
            student: str
            device, action = qr_proc.process_code(qr_proc.read_code("Show Chromebook"), "device")
            student = qr_proc.process_code(qr_proc.read_code("Show ID"), "student")

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

            update(entry, calc_sheet) if "CALC-" in device else update(entry, cb_sheet)

            # Update dicts in charge of keeping track of whether a device is rented out or not
            devices: dict[str, str] = {}

            devices.update(
                zip(
                    [name.value for name in cb_sheet.range(f"G2:G{lr_cb}")],
                    cb_sheet.range(f"H2:H{lr_cb}")
                )
            )

            devices.update(
                zip(
                    [name.value for name in calc_sheet.range(f"G2:G{lr_calc}")],
                    calc_sheet.range(f"H2:H{lr_calc}")
                )
            )

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
