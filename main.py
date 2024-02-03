import cv2
import gspread
from tools import *
from datetime import datetime


if __name__ == "__main__":
    print(f"\n{TC.OK}[INFO]{TC.ENDC}\tSetting things up")

    # variables
    entry: dict = {}
    devices: dict = {}

    # file i/o
    decrypt = read_json("resources/data/validation.json")
    settings = read_json("resources/data/settings.json")

    # cv2
    decoder: cv2.QRCodeDetector = cv2.QRCodeDetector()

    # gspread setup
    client: gspread.service_account = gspread.service_account_from_dict(read_json("resources/data/api_key.json"))
    cb_sheet: gspread.Worksheet = client.open("Chromebook Tracker").worksheet(settings["chromebook sheet"])
    calc_sheet: gspread.Worksheet = client.open("Chromebook Tracker").worksheet(settings["calculator sheet"])

    # gspread reading
    lr_cb = len(cb_sheet.col_values(7))
    lr_calc = len(calc_sheet.col_values(7))
    devices.update(zip([name.value for name in cb_sheet.range(f"G2:G{lr_cb}")], cb_sheet.range(f"H2:H{lr_cb}")))
    devices.update(zip([name.value for name in calc_sheet.range(f"G2:G{lr_calc}")], calc_sheet.range(f"H2:H{lr_calc}")))

    while True:
        try:
            # TODO: On slower devices need to release cam or it will carry the last scan into next call of read_code
            # TODO: See if there is a way to work around this

            # Get device
            cam = cv2.VideoCapture(0)
            device, action = read_code(cam, decoder, "Show Chromebook/Calculator", decrypt, devices, "device")
            cam.release()

            # Get student
            cam = cv2.VideoCapture(0)
            student, _ = read_code(cam, decoder, "Show ID", decrypt, devices, "student")
            cam.release()

            cv2.waitKey(500)
            show_proc_img("resources/img/updating.png")
            cv2.waitKey(1)

            current_time = datetime.now()
            entry["action"] = action
            entry["device"] = device
            entry["date"] = f"{current_time.day}/{current_time.month}/{current_time.year}"
            entry["student"] = student
            entry["time"] = f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}"

            update_sheet(entry, calc_sheet) if "CALC-" in device else update_sheet(entry, cb_sheet)

            # Update dicts in charge of keeping track of whether a device is rented out or not
            devices = {}
            devices.update(zip([name.value for name in cb_sheet.range(f"G2:G{lr_cb}")], cb_sheet.range(f"H2:H{lr_cb}")))
            devices.update(zip([name.value for name in calc_sheet.range(f"G2:G{lr_calc}")], calc_sheet.range(f"H2:H{lr_calc}")))

        except cv2.error:
            print(f"{TC.WARNING}[WARN]{TC.ENDC}\tOpenCV threw some errors, can likely ignore")

        except (Exception,):
            cv2.destroyAllWindows()
            print(f"{TC.FAIL}[FATAL]{TC.ENDC}\tUnknown error occurred. See logs for more details")
            print(f"{TC.OK}[INFO]{TC.ENDC}\tRestarting in 5 seconds...")
            time.sleep(5)
            write_log()
            continue

