import json
import gspread
import cv2
import threading
import numpy as np
from colouring import TC
from threading import Timer, Thread


def read_json(path: str, exit_on_err=True) -> dict | list:
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"{TC.FAIL}[ERROR]\tFile {path} could not be found{TC.ENDC}")
        exit(1)

    except json.JSONDecodeError:
        if exit_on_err:
            print(f"{TC.FAIL}[ERROR]\tFile {path} is not valid or is empty{TC.ENDC}")
            exit(1)
        else:
            print(f"{TC.WARNING}[WARN]\tFile {path} is empty{TC.ENDC}")
            return []


def write_json(path: str, data: dict) -> None:
    with open(path, "w") as f:
        try:
            json.dump(data, f, indent=4)

        except Exception as err:
            print(f"{TC.FAIL}[ERROR]\tCould not write json -> {TC.ENDC}{err}")


def update_sheet(update_interval) -> None:
    print(f"{TC.OKGREEN}[INFO]{TC.ENDC}\tUpdating sheet")

    # Read files
    batch: dict = read_json("./resources/data/batch.json", exit_on_err=False)
    statuses: dict = read_json("./resources/data/status.json")
    settings: dict = read_json("./resources/data/settings.json")

    # Spreadsheet api setup
    client = gspread.service_account_from_dict(read_json("./resources/data/api_key.json"))
    sheet = client.open("Chromebook Tracker").worksheet(settings["sheet"])

    # Get all cells to be modified
    last_row = len(sheet.col_values(1)) + 1
    status_cells = sheet.range(f"H2:{len(sheet.col_values(8))}")
    info_grid = [sheet.range(f"A{last_row + i}:E{last_row + i}") for i in range(len(batch))]

    # Set the batch cells
    for i, row in enumerate(info_grid):
        row[0].value = batch[i]["chromebook"]
        row[1].value = batch[i]["action"]
        row[2].value = batch[i]["student"]
        row[3].value = batch[i]["date"]
        row[4].value = batch[i]["time"]

    # Set the status cells
    for i, val in enumerate(statuses.values()):
        status_cells[i].value = val

    # Merge the two together to update all at once
    for i in info_grid:
        status_cells.extend(i)

    # Update all modified cells
    sheet.update_cells(status_cells)

    # Eat batch values
    with open("./resources/data/batch.json", "w"):
        pass

    print(f"{TC.OKGREEN}[INFO]{TC.ENDC}\tFinished updating sheet")
    print(f"{TC.OKGREEN}[INFO]{TC.ENDC}\tRestarting timer")
    for thr in threading.enumerate():
        if isinstance(thr, threading.Timer):
            thr.cancel()

    update_queue = Timer(update_interval, update_sheet, args=[update_interval])
    update_queue.daemon = True
    update_queue.start()


def show_proc_img(proc_img: np.array, msg: str) -> None:
    img = cv2.putText(proc_img.copy(), msg,
                      [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                      [0, 0, 0], 1, cv2.LINE_AA)
    cv2.imshow("Scanner", img)


def read_code(cam: cv2.VideoCapture, decoder: cv2.QRCodeDetector,
              msg: str, hash_dict: dict, status_dict: dict,
              proc_img: np.array, update_interval: float) -> str | tuple[str, str]:
    while True:
        _, raw_frame = cam.read()
        raw_result, _, _ = decoder.detectAndDecode(raw_frame)
        status_flip = {"IN": "OUT", "OUT": "IN"}
        if raw_frame is None:
            print(f"{TC.FAIL}[ERROR]\t{TC.ENDC}Could not read camera")
            cv2.destroyAllWindows()
            cam.release()
            exit(1)

        else:
            if raw_result == "":
                frame = cv2.flip(raw_frame, 1)
                cv2.putText(frame, msg,
                            [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                            [0, 0, 0], 1, cv2.LINE_AA)
                cv2.putText(frame, "Press 'u' to update",
                            [10, 60], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                            [0, 0, 0], 1, cv2.LINE_AA)
                cv2.putText(frame, "Press 'q' to quit",
                            [10, 90], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                            [0, 0, 0], 1, cv2.LINE_AA)
                cv2.imshow("Scanner", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    cam.release()
                    update_sheet(update_interval)
                    print(f"{TC.OKGREEN}[INFO]{TC.ENDC}\tTimer killed. Exiting")
                    exit(0)

                elif key == ord('u'):
                    if len(threading.enumerate()) < 3:
                        (Thread(target=update_sheet, args=[update_interval])).start()

                    else:
                        print(f"{TC.WARNING}[WARN]\tUpdate thread already running. Ignoring request{TC.ENDC}")

            else:
                if raw_result in hash_dict:
                    show_proc_img(proc_img.copy(), f"Obtained: {(unhashed := hash_dict[raw_result])}")
                    if cv2.waitKey(1000) & 0xFF == 27:
                        pass
                    return unhashed

                elif raw_result in status_dict:
                    status_dict[raw_result] = status_flip[status_dict[raw_result]]
                    write_json("./resources/data/status.json", status_dict)
                    show_proc_img(proc_img.copy(), f"Obtained: {raw_result}")
                    if cv2.waitKey(1000) & 0xFF == 27:
                        pass
                    return raw_result, status_dict[raw_result]
