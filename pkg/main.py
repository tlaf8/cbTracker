from tools import *
from datetime import datetime


class TC:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


if __name__ == "__main__":
    decoder: cv2.QRCodeDetector = cv2.QRCodeDetector()
    proc_img: np.array = cv2.imread("resources/img/scan_img.png")
    loading_img: np.array = cv2.imread("resources/img/loading.png")
    decrypt: dict = read_json("resources/data/validation.json")
    settings: dict = read_json("resources/data/settings.json")
    client: gspread.service_account = gspread.service_account_from_dict(read_json("resources/data/api_key.json"))
    sheet: gspread.Worksheet = client.open("Chromebook Tracker").worksheet(settings["sheet"])
    lr_status: int = len(sheet.col_values(7))
    chromebooks: dict = dict(
        zip([name.value for name in sheet.range(f"G2:G{lr_status}")], sheet.range(f"H2:H{lr_status}"))
    )
    entry: dict = {}

    while True:
        try:
            cam = cv2.VideoCapture(0)
            cb, action = read_code(cam, decoder, "Show Chromebook", decrypt, chromebooks, proc_img)
            cam.release()

            cam = cv2.VideoCapture(0)
            student = read_code(cam, decoder, "Show ID", decrypt, chromebooks, proc_img)
            cam.release()

            show_proc_img(loading_img, "")
            if cv2.waitKey(1) & 0xFF == 27:
                pass

            current_time = datetime.now()
            entry["action"] = action
            entry["chromebook"] = cb
            entry["date"] = f"{current_time.day}/{current_time.month}/{current_time.year}"
            entry["student"] = student
            entry["time"] = f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}"

            update_sheet(entry, sheet)
            chromebooks = dict(
                zip([name.value for name in sheet.range(f"G2:G{lr_status}")], sheet.range(f"H2:H{lr_status}"))
            )

        except cv2.error:
            print(f"{TC.WARNING}[WARN]{TC.ENDC} OpenCV threw error, can likely ignore")

        except ValueError:
            print(f"{TC.FAIL}[ERROR]{TC.ENDC} Not scanning in right order. Check logs for more info")

            with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
                traceback.print_exc(file=log)

            show_proc_img(loading_img, "Follow on screen instructions. Restarting")
            if cv2.waitKey(1500) & 0xFF == 27:
                pass

        except Exception:
            print(f"{TC.FAIL}[FATAL]{TC.ENDC} Unknown error occurred. See logs for more details")

            with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
                traceback.print_exc(file=log)

            exit(1)

