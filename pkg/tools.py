import json
import time
import cv2
import numpy as np
import traceback
from main import TC


def read_json(path: str, exit_on_err=True) -> dict | list:
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tFile {path} could not be found. Check logs for more info")

        with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
            traceback.print_exc(file=log)

        exit(1)

    except json.JSONDecodeError:
        if exit_on_err:
            print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tFile {path} invalid or empty. Check logs for more info")

            with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
                traceback.print_exc(file=log)

            exit(1)

        else:
            print(f"{TC.WARNING}[WARN]{TC.ENDC}\tFile {path} is empty")
            return []


def write_json(path: str, data: dict) -> None:
    with open(path, "w") as f:
        try:
            json.dump(data, f, indent=4)

        except (Exception,):
            print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tCould not write json. Check logs for more info")

            with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
                traceback.print_exc(file=log)

            exit(1)


def update_sheet(entry, sheet) -> None:
    print(f"{TC.OK}[INFO]{TC.ENDC}\tUpdating sheet")

    # Go from H2 to the end of data in column H
    status_lr: int = len(sheet.col_values(8))
    status_cells: dict = dict(
        zip([name.value for name in sheet.range(f"G2:G{status_lr}")], sheet.range(f"H2:H{status_lr}"))
    )

    # Grab last row + 1 from A to E
    data_lr: int = len(sheet.col_values(1))
    entry_cells: list = sheet.range(f"A{data_lr + 1}:E{data_lr + 1}")

    # Set status cell value
    status_cells[entry["chromebook"]].value = entry["action"]

    # Set values to data given in entry accordingly
    entry_cells[0].value = entry["chromebook"]
    entry_cells[1].value = entry["action"]
    entry_cells[2].value = entry["student"]
    entry_cells[3].value = entry["date"]
    entry_cells[4].value = entry["time"]

    # Update the sheet with new values
    sheet.update_cells(list(status_cells.values()) + entry_cells)

    print(f"{TC.OK}[INFO]{TC.ENDC}\tFinished updating sheet")


def show_proc_img(proc_img: np.array, msg: str) -> None:
    img = cv2.putText(proc_img.copy(), msg,
                      [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                      [0, 0, 0], 1, cv2.LINE_AA)
    cv2.imshow("Scanner", img)


def read_code(cam: cv2.VideoCapture, decoder: cv2.QRCodeDetector,
              msg: str, hash_dict: dict, status_dict: dict,
              proc_img: np.array) -> str | tuple[str, str]:
    while True:
        _, raw_frame = cam.read()
        raw_result, _, _ = decoder.detectAndDecode(raw_frame)
        status_flip = {"IN": "OUT", "OUT": "IN"}
        if raw_frame is None:
            print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tCould not read camera")

            with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
                traceback.print_exc(file=log)

            cv2.destroyAllWindows()
            cam.release()
            exit(1)

        else:
            settings = read_json("resources/data/settings.json")
            if raw_result == "":
                frame = cv2.flip(raw_frame, 1)

                cv2.namedWindow("Scanner", flags=cv2.WINDOW_GUI_NORMAL)
                cv2.resizeWindow("Scanner", settings["window x"], settings["window y"])
                cv2.putText(frame, msg,
                            [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                            [0, 0, 0], 1, cv2.LINE_AA)
                cv2.putText(frame, "Press 'q' to quit",
                            [10, 60], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                            [0, 0, 0], 1, cv2.LINE_AA)

                cv2.imshow("Scanner", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    cam.release()
                    print(f"{TC.OK}[INFO]{TC.ENDC}\tExiting")
                    exit(0)

            else:
                print(f"{TC.OK}[INFO]{TC.ENDC}\tRead value: {raw_result}")
                if raw_result in hash_dict:
                    show_proc_img(proc_img.copy(), f"Obtained: {(decrypt := hash_dict[raw_result])}")
                    if cv2.waitKey(1500) & 0xFF == 27:
                        pass
                    return decrypt

                elif raw_result in status_dict:
                    action: str = status_flip[status_dict[raw_result].value]
                    show_proc_img(proc_img.copy(), f"Obtained: {raw_result}")
                    if cv2.waitKey(1500) & 0xFF == 27:
                        pass
                    return raw_result, action
