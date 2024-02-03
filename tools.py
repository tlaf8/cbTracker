import os
import json
import time
import cv2
import base64
import requests
import traceback
import qrcode as qr
from hashlib import sha256
from pwinput import pwinput
from PIL import Image, ImageDraw, ImageFont


class TC:
    OK = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    HELP = '\033[36m'
    WARNING = '\033[93m'


def write_log() -> None:
    try:
        with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
            traceback.print_exc(file=log)

    except FileNotFoundError:
        os.mkdir("logs")
        write_log()


def read_txt(path: str) -> tuple[list[str], list[str]]:
    with open(path, 'r') as file_in:
        return [line for line in file_in if line[0] != '#'], [line for line in file_in if line[0] == '#']


def read_json(path: str, exit_on_err=True) -> dict[str: str] | list:
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"{TC.FAIL}[ERROR]{TC.ENDC}\tFile {path} could not be found. Check logs for more info")

        if "validation.json" in path or "api_key.json" in path:
            if input(f"{TC.HELP}[HELP]{TC.ENDC}\tLooks like {path} is missing. Download it? (y/n) ").lower() == "y":
                sync_local(pwinput())
                print(f"{TC.OK}[INFO]{TC.ENDC}\tFiles downloaded successfully. Please restart the program.")
                print(f"{TC.OK}[INFO]{TC.ENDC}\tExiting in 5")
                time.sleep(5)
                exit(0)

            else:
                exit(0)

        else:
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


def sync_local(pwd: str) -> None:
    returned = requests.post("https://tryobgwrhsrnbyq5re77znzxry0brhfc.lambda-url.ca-central-1.on.aws/",
                             data={"pass": sha256(pwd.encode()).hexdigest()}).content.decode("utf-8")

    if returned == "Unauthorized: Bad password":
        print(f"{TC.FAIL}[ERROR]{TC.ENDC}\t{returned}")
        exit(1)

    returned = json.loads(returned)
    api_key = json.loads(returned["api_key"])
    validation = json.loads(returned["validation"])

    write_json("resources/data/api_key.json", api_key)
    write_json("resources/data/validation.json", validation)


def update_sheet(entry, sheet) -> None:
    print(f"{TC.OK}[INFO]{TC.ENDC}\tUpdating sheet")

    # Go from H2 to the end of data in column H
    status_lr = len(sheet.col_values(8))
    status_cells = dict(zip([name.value for name in sheet.range(f"G2:G{status_lr}")], sheet.range(f"H2:H{status_lr}")))

    # Grab last row + 1 from A to E, using A as search column
    data_lr = len(sheet.col_values(1))
    entry_cells = sheet.range(f"A{data_lr + 1}:E{data_lr + 1}")

    # Set status cell value
    status_cells[entry["device"]].value = entry["action"]

    # Set values to data given in entry accordingly
    entry_cells[0].value = entry["device"]
    entry_cells[1].value = entry["action"]
    entry_cells[2].value = entry["student"]
    entry_cells[3].value = entry["date"]
    entry_cells[4].value = entry["time"]

    # Update the cb_sheet with new values
    sheet.update_cells(list(status_cells.values()) + entry_cells)

    print(f"{TC.OK}[INFO]{TC.ENDC}\tFinished updating sheet")


def show_proc_img(img_path: str, msg: str = "") -> None:
    img = cv2.putText(img=cv2.imread(img_path),
                      text=msg,
                      org=[10, 30],
                      fontFace=cv2.FONT_HERSHEY_DUPLEX,
                      fontScale=0.75,
                      color=[0, 0, 0],
                      thickness=1,
                      lineType=cv2.LINE_AA)
    cv2.imshow("Scanner", img)


def read_code(cam: cv2.VideoCapture,
              decoder: cv2.QRCodeDetector,
              msg: str,
              hash_dict: dict,
              status_dict: dict,
              expecting: str) -> tuple[str, str]:
    settings = read_json("resources/data/settings.json")
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
            if raw_result == "":
                frame = cv2.flip(raw_frame, 1)

                cv2.namedWindow("Scanner", flags=cv2.WINDOW_GUI_NORMAL)
                cv2.resizeWindow("Scanner", settings["window x"], settings["window y"])
                cv2.putText(img=frame,
                            text=msg,
                            org=[10, 30],
                            fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.75,
                            color=[0, 0, 0],
                            thickness=1,
                            lineType=cv2.LINE_AA)
                cv2.putText(img=frame,
                            text="Press 'q' to quit",
                            org=[10, 60],
                            fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.75,
                            color=[0, 0, 0],
                            thickness=1,
                            lineType=cv2.LINE_AA)

                cv2.imshow("Scanner", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    cam.release()
                    print(f"{TC.OK}[INFO]{TC.ENDC}\tExiting")
                    exit(0)

                elif key == ord('s'):
                    cv2.destroyAllWindows()
                    cam.release()
                    if input("Sync local machine with AWS? (y/n) ").lower() == "y":
                        aws_key = pwinput()
                        sync_local(aws_key)
                        print("Finished syncing local machine")

                    if input("Sync AWS with local machine? (y/n) ").lower() == "y":
                        aws_key = pwinput()
                        upload_data(read_json("resources/data/validation.json", exit_on_err=True), "validation", aws_key)
                        upload_data(read_json("resources/data/api_key.json", exit_on_err=True), "apikey", aws_key)
                        print("Finished syncing AWS")

                elif key == ord('n'):
                    cv2.destroyAllWindows()
                    cam.release()
                    create_qr_codes("resources/qr_codes/output", fuzz=pwinput("Fuzzer: "))

            else:
                print(f"{TC.OK}[INFO]{TC.ENDC}\tRead value: {raw_result}")
                if raw_result in hash_dict:  # Student ID was scanned
                    show_proc_img("resources/img/scan_img.png", f"Obtained: {(decrypt := hash_dict[raw_result])}")
                    cv2.waitKey(500)

                    if expecting == "student":
                        return decrypt, ""  # Return empty string for consistency

                    else:
                        show_proc_img("resources/img/loading.png", "Expected a device")
                        cam.release()
                        cv2.waitKey(3000)

                elif raw_result in status_dict:  # Device was scanned
                    action = status_flip[status_dict[result := raw_result].value]
                    show_proc_img("resources/img/scan_img.png", f"Obtained: {result}")
                    cv2.waitKey(500)

                    if expecting == "device":
                        return result, action

                    else:
                        show_proc_img("resources/img/loading.png", "Expected an ID")
                        cam.release()
                        cv2.waitKey(3000)


def upload_data(data: dict, kind: str, pwd: str) -> str:
    params = {
        "pass": sha256(pwd.encode()).hexdigest(),
        "kind": kind,
        "data": base64.urlsafe_b64encode(json.dumps(data).encode())
    }

    resp = requests.post("https://i5nqbfht5a6v4epzr5anistot40qkyaz.lambda-url.ca-central-1.on.aws/", data=params)
    return resp.content.decode("utf-8")


def create_qr_codes(path_out: str, fuzz: str = None, from_file=False) -> None:
    font = ImageFont.truetype("resources/data/RobotoMono-Regular.ttf", size=16)

    # DO NOT REMOVE! Code created courtesy of developer and princess Lily
    # help(code)

    if from_file is True:
        names, comments = read_txt("resources/qr_codes/creation_list.txt")
        open("resources/qr_codes/creation_list.txt", 'w').close()
        with open("resources/qr_codes/creation_list.txt", 'w') as creation_list:
            creation_list.writelines(comments)

    else:
        names = []
        print("Enter 'DONE' or nothing when finished.")
        while True:
            if (name := input("Enter full name of student/device: ")) == "DONE" or name == "":
                break

            elif len(name.split(" ")) < 2:
                print("Only found 1 name. Ensure that first, last and other names are entered")

            else:
                names.append(" ".join([i.strip() for i in name.split()]))

    print("Creating QR codes for the following names:")
    for name in names:
        print(f"  --> {name}")

    if input("Continue? (y/n) ").lower() != 'y':
        return

    for entry in names:
        stripped = entry.strip()

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

            if data in validation_json:
                print("Name already exists. Regenerating QR code")
                qr.make(data).save(f"{path_out}/{stripped}.png")

            validation_json[data] = stripped
            write_json("resources/data/validation.json", validation_json)
            upload_data(validation_json, "validation", pwinput())

        else:
            qr.make(stripped).save(f"{path_out}/{stripped}.png")

        img = Image.open(f"{path_out}/{entry}.png")
        printer = ImageDraw.Draw(img)
        printer.text((img.width / 2 - font.getlength(entry) / 2, img.height - 30), entry, font=font)
        img.save(f"{path_out}/{entry}.png")
