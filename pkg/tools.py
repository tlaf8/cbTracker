import os
import json
import time
import cv2
import numpy as np
import qrcode as qr
import traceback
from PIL import Image, ImageDraw, ImageFont
from hashlib import sha256


class TC:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def write_log() -> None:
    try:
        with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
            traceback.print_exc(file=log)

    except FileNotFoundError:
        os.mkdir("logs")
        write_log()


def read_txt(path: str) -> tuple[list[str], list[str]]:
    with open(path, 'r') as file_in:
        content = []
        comments = []

        for line in file_in:
            if '#' in line:
                comments.append(line)

            else:
                content.append(line)

    return content, comments


def read_json(path: str, exit_on_err=True) -> dict | list:
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tFile {path} could not be found. Check logs for more info")
        write_log()
        exit(1)

    except json.JSONDecodeError:
        if exit_on_err:
            print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tFile {path} invalid or empty. Check logs for more info")
            write_log()
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
            write_log()
            exit(1)


def update_sheet(entry, sheet) -> None:
    print(f"{TC.OK}[INFO]{TC.ENDC}\tUpdating sheet")

    # Go from H2 to the end of data in column H
    status_lr = len(sheet.col_values(8))
    status_cells = dict(
        zip([name.value for name in sheet.range(f"G2:G{status_lr}")], sheet.range(f"H2:H{status_lr}"))
    )

    # Grab last row + 1 from A to E
    data_lr = len(sheet.col_values(1))
    entry_cells = sheet.range(f"A{data_lr + 1}:E{data_lr + 1}")

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
            write_log()
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
                    print(f"{TC.OK}[INFO]{TC.ENDC} Exiting")
                    exit(0)

                elif key == ord('U'):
                    cv2.destroyAllWindows()
                    cam.release()
                    match input("Check for updates? (y/n) ").lower():
                        case 'y':
                            print(f"{TC.OK}[INFO]{TC.ENDC} Running update")
                            exit(0)

                        case 'n':
                            print(f"{TC.OK}[INFO]{TC.ENDC} Abort")
                            continue

                        case _:
                            print(f"{TC.OK}[INFO]{TC.ENDC} Unknown key. Aborting")
                            continue

            else:
                print(f"{TC.OK}[INFO]{TC.ENDC}\tRead value: {raw_result}")
                if raw_result in hash_dict:
                    show_proc_img(proc_img.copy(), f"Obtained: {(decrypt := hash_dict[raw_result])}")
                    if cv2.waitKey(1500) & 0xFF == 27:
                        pass
                    return decrypt

                elif raw_result in status_dict:
                    action = status_flip[status_dict[raw_result].value]
                    show_proc_img(proc_img.copy(), f"Obtained: {raw_result}")
                    if cv2.waitKey(1500) & 0xFF == 27:
                        pass
                    return raw_result, action


def create_qr_codes(path_out: str, fuzz: str = None):
    filenames = []
    font = ImageFont.truetype("resources/data/RobotoMono-Regular.ttf", size=16)

    # DO NOT REMOVE! Code created courtesy of developer Lily
    #
    # help(code)
    #
    #

    content, comments = read_txt("resources/qr_codes/creation_list.txt")
    open("resources/qr_codes/creation_list.txt", 'w').close()
    with open("resources/qr_codes/creation_list.txt", 'w') as creation_list:
        creation_list.writelines(comments)

    for entry in content:
        stripped = entry.strip()
        filenames.append(stripped)

        if fuzz != "":
            try:
                qr.make(
                    data := sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                ).save(f"{path_out}/{stripped}.png")

            except FileNotFoundError:
                print("Path invalid. Defaulting")
                qr.make(
                    data := sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                ).save(f"resources/qr_codes/output/{stripped}.png")

            validation_json = read_json("resources/data/validation.json", exit_on_err=True)
            while True:
                if data in validation_json:
                    print("Key exists already somehow. Reversing fuzz and trying again")
                    qr.make(
                        data := sha256((fuzz[::-1]).join(stripped.split()).encode()).hexdigest()
                    ).save(f"{path_out}/{stripped}.png")
                    continue

                else:
                    break

            validation_json[data] = stripped
            write_json("resources/data/validation.json", validation_json)

        else:
            qr.make(stripped).save(f"{path_out}/{stripped}.png")

    for file in filenames:
        img = Image.open(f"{path_out}/{file}.png")
        printer = ImageDraw.Draw(img)
        printer.text((img.width / 2 - font.getlength(file) / 2, img.height - 30), file, font=font)
        img.save(f"{path_out}/{file}.png")


if __name__ == "__main__":
    print("This file only contains helper functions and is useless unless generating qr codes.")
    match input("Create QR codes? (y/n) ").lower():
        case 'y':
            modifier = input("Enter desired name modifier (Leave blank for none): ")
            if (output_path := input("Enter output path (Leave blank for default): ").lower()) != "":
                create_qr_codes(output_path, modifier)
            else:
                create_qr_codes("resources/qr_codes/output", modifier)

        case 'n':
            exit(0)

        case _:
            print("Invalid option. Exiting")
            exit(0)
