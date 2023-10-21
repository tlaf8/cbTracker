import cv2
import json
import gspread
import subprocess as sp
from sys import exit
from time import sleep
from base64 import b64decode, b64encode
from datetime import datetime
from tools.common import obtain_auth, read_file, get_statuses


VERBOSE = False
SLEEP_TIME = 1


def run_update() -> sp.Popen | None:
    print("Starting update procedure...")
    print(f"Running with {len(batch)} entries.")
    if len(batch) == 0:
        print("No entries found in batch")

        if update_mode == 'q':
            exit("No errors occurred on main script.")

        elif update_mode == 'u':
            return None

    packaged = b64encode(" -- ".join([" | ".join(i) for i in batch]).encode()).decode()
    final_statuses = b64encode(json.dumps(statuses).encode()).decode()
    try:
        task = sp.Popen(
            f"./venv/bin/python ./tools/sheet_updater.py {packaged} {final_statuses}".split()
        )

    except FileNotFoundError:
        task = sp.Popen(
            f"./venv/Scripts/python.exe ./tools/sheet_updater.py {packaged} {final_statuses}".split()
        )

    return task


def read_code(message: str) -> str:
    cam = cv2.VideoCapture(0)
    while True:
        try:
            _, frame = cam.read()
            data, _, _ = reader.detectAndDecode(frame)

        except cv2.error:
            continue

        if len(data) > 0:
            cam.release()
            return data

        frame = cv2.flip(frame, 1)
        cv2.putText(
            frame,
            message,
            [10, 30],
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            [0, 0, 0],
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press 'q' to quit.",
            [10, 60],
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            [0, 0, 0],
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press 'u' to force update.",
            [10, 90],
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            [0, 0, 0],
            1,
            cv2.LINE_AA,
        )
        cv2.imshow("cbTracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            update_mode = 'q'
            cam.release()
            cv2.destroyAllWindows()
            proc = run_update()
            if proc is not None:
                while proc.poll() is None:
                    sleep(0.5)

            exit("No errors occurred on main script.")

        elif key == ord('u'):
            update_mode = 'u'
            run_update()
            batch.clear()


if __name__ == "__main__":
    temps = []
    room = None
    update_mode = 'u'
    reader = cv2.QRCodeDetector()
    decrypt = {v: k for k, v in read_file("./resources/validations/validation.json").items()}

    cv2.namedWindow("cbTracker", cv2.WINDOW_GUI_NORMAL)

    if VERBOSE is True:
        print("Reading settings")

    try:
        for line in read_file("./resources/settings.txt"):
            if "QR Code" in line:
                temps.append(line)

            elif "Room number" in line:
                room = line.split("Room number: ")[1]

            else:
                raise ValueError

    except ValueError:
        print("Invalid settings file. Please review and try again.")
        input("Press ENTER to exit...")
        exit("Formatting error.")

    client = gspread.service_account_from_dict(
        json.loads(b64decode(obtain_auth("./resources/gspread_auth.txt")))
    )
    sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")
    statuses = get_statuses(sheet)
    status_cells = {f"SF{room}-{i}": f"8{i + 1}" for i in range(1, 7, 1)}
    status_cells.update({f"SFRED-{i}": f"8{i + 7}" for i in range(1, 33, 1)})
    temps_dict = {
        f"student{i + 1}": val.split(":")[1].strip() for i, val in enumerate(temps)
    }
    status_rev = {"OUT": "IN", "IN": "OUT"}
    last_row = len(sheet.col_values(1))

    if VERBOSE is True:
        print("Opening camera")

    global batch
    batch = []
    statuses = get_statuses(sheet)
    while True:
        chromebook = read_code("Please show chromebook")
        sleep(SLEEP_TIME)
        encoded = read_code("Please show ID")
        sleep(SLEEP_TIME)

        if VERBOSE is True:
            print("Verifying inputs")

        if encoded not in decrypt:
            print("QR code not recognized. Please get teacher to look into this.")
            print(f"Read: {encoded}. Restarting in 3")
            sleep(3)
            continue

        if encoded in temps_dict:
            encoded = temps_dict[encoded]

        date = datetime.today()
        statuses[chromebook] = status_rev[statuses[chromebook]]
        last_row += 1
        batch.append(
            [
                room,
                chromebook,
                statuses[chromebook],
                decrypt[encoded],
                f"{f'{date.month:02d}'}/{f'{date.day:02d}'}/{f'{date.year:02d}'}",
                f"{f'{date.hour:02d}'}:{f'{date.minute:02d}'}:{f'{date.second:02d}'}",
                str(last_row),
                status_cells[chromebook],
            ]
        )

        if len(batch) >= 3:
            run_update()
            batch.clear()
