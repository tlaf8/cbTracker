import gspread
import cv2
import json
from json.decoder import JSONDecodeError
from sys import exit
from base64 import b64decode
from datetime import datetime


def read_file(path: str) -> list | dict:
    try:
        with open(path, "r") as file:
            if ".json" not in path:
                return [ln.rstrip() for ln in file.readlines() if ln != "\n" and "#" not in ln]

            else:
                return json.load(file)

    except (FileNotFoundError, JSONDecodeError) as error:
        print("File could not be found or JSON is not properly formatted. See below for full error.")
        print(error)
        input("Press ENTER to exit...")
        exit(1)


def read_code(message: str) -> str:
    cam = cv2.VideoCapture(0)
    reader = cv2.QRCodeDetector()

    while True:
        _, frame = cam.read()
        data, _, _ = reader.detectAndDecode(frame)

        frame = cv2.flip(frame, 1)
        cv2.putText(
            frame,
            message,
            [10, 30],
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            [0, 0, 0],
            1,
            cv2.LINE_AA
        )
        cv2.putText(
            frame,
            "Press 'q' to quit.",
            [10, 60],
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            [0, 0, 0],
            1,
            cv2.LINE_AA
        )
        cv2.imshow("Scanner", frame)
        cv2.setWindowProperty("Scanner", cv2.WND_PROP_TOPMOST, 1)

        if len(data) > 0:
            return data

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            exit(0)


def obtain_auth() -> str:
    try:
        with open("./gspread_auth.txt", "r") as auth:
            return auth.readlines()[0].strip()

    except FileNotFoundError:
        try:
            with open("../resources/gspread_auth.txt", "r") as auth:
                return auth.readlines()[0].strip()

        except FileNotFoundError:
            print("GSpread authentication could not be found. Please contact 21laforgth@gmail.com.")


def update_sheet(sheet_obj: gspread.worksheet.Worksheet, cb_id: str, student: str) -> None:
    try:
        cb = status_cells[cb_id]
        sheet_obj.update_cell(cb[1], cb[0], status_rev[sheet_obj.cell(cb[1], cb[0]).value])
        sheet_obj.update_cell(last_row, 1, cb_id)
        sheet_obj.update_cell(last_row, 2, sheet_obj.cell(cb[1], cb[0]).value)
        sheet_obj.update_cell(last_row, 3, student)
        sheet_obj.update_cell(
            last_row,
            4,
            f"{'{:02d}'.format(date.month)}/{'{:02d}'.format(date.day)}/{'{:02d}'.format(date.year)}"
        )
        sheet_obj.update_cell(
            last_row,
            5,
            f"{'{:02d}'.format(date.hour)}:{'{:02d}'.format(date.minute)}:{'{:02d}'.format(date.second)}"
        )

    except Exception as e:
        print(f"Something went wrong. Exception:\n\t{type(e).__name__} --> {e}")
        cv2.destroyAllWindows()
        exit(4)


if __name__ == "__main__":
    verbose = False if input("Run in verbose mode? (y/n) ") == "n" else True

    if verbose is True:
        print("Reading settings")

    lines = read_file("./resources/settings.txt")
    temps = []
    room = -1

    try:
        for line in lines:
            if "QR Code" in line:
                temps.append(line)

            elif "Room" in line:
                room = int(line.split(":")[1].strip())

            else:
                if verbose is True:
                    print("Unexpected value found in settings. Please review the file.")

                input("Press ENTER to exit...")
                exit(2)

    except ValueError:
        print("Unexpected value for room number in settings.txt. Please check and run again.")
        input("Press ENTER to exit...")
        exit(3)

    status_cells = {f"SF{room}-{i}": f"8{i + 1}" for i in range(1, 7, 1)}
    status_cells.update({f"SFRED-{i}": f"8{i + 7}" for i in range(1, 33, 1)})
    status_rev = {"OUT": "IN", "IN": "OUT"}
    temps_dict = {f"student{i + 1}": val.split(":")[1].strip() for i, val in enumerate(temps)}
    decrypt = {v: k for k, v in read_file("./resources/outputs/validation.json").items()}
    date = datetime.today()

    if verbose is True:
        print("Starting gspread client")

    client = gspread.service_account_from_dict(json.loads(b64decode(obtain_auth())))
    sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")

    if verbose is True:
        print("Opening camera")

    while True:
        # try:
        #     # Try this method to search for dates (hopefully faster).
        #     last_row = sheet.findall(
        #         f"{'{:02d}'.format(date.month)}/{'{:02d}'.format(date.day)}/{'{:02d}'.format(date.year)}"
        #     )[-1].row + 1
        #
        # except IndexError:
        #     # Use this method as a backup. Gets a list of all elements in a column and gets the length.
        #     last_row = len(sheet.col_values(1)) + 1

        last_row = len(sheet.col_values(1)) + 1
        chromebook = read_code("Please show chromebook")
        encoded = read_code("Please show ID")

        if verbose is True:
            print("Verifying inputs")

        if encoded not in decrypt:
            print("QR code not recognized. Please get teacher to look into this.")
            continue

        if encoded in temps_dict:
            encoded = temps_dict[encoded]

        update_sheet(sheet, chromebook, decrypt[encoded])

