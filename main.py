import gspread
import cv2
import json
import qrcode
import hashlib
from sys import exit
from datetime import datetime
from time import sleep


def read_json(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        print("File could not be found.")
        print("Exiting in 10 seconds (You can close this window)")
        sleep(10)
        exit(5)


def read_file(path: str) -> list:
    try:
        with open(path, "r") as file:
            return [line.rstrip() for line in file.readlines() if line != "\n" and "#" not in line]

    except FileNotFoundError:
        print("File could not be found.")
        print("Exiting in 10 seconds (You can close this window)")
        sleep(10)
        exit(5)


def write_file(path: str, obj: dict):
    try:
        with open(path, "a") as file:
            json.dump(obj, file)

    except FileNotFoundError:
        print("File could not be found.")
        print("Exiting in 10 seconds (You can close this window)")
        sleep(10)
        exit(5)


def generate_qr_codes():
    lines = read_file(r"resources/classlist.txt")
    secret = input("Please enter a secret to encrypt with: ")
    open("resources/validation.json", "w").close()

    codes = {}
    for entry in lines:
        temp = hashlib.sha256((entry + secret).encode()).hexdigest()
        qrcode.make(temp).save(rf"resources/qr_codes/{entry}.png")
        codes[entry] = temp

    write_file(r"resources/validation.json", {v: k for k, v in codes.items()})


def read_code(message: str):
    cam = cv2.VideoCapture(0)
    reader = cv2.QRCodeDetector()

    while True:
        _, frame = cam.read()
        data, _, _ = reader.detectAndDecode(frame)

        frame = cv2.flip(frame, 1)
        cv2.putText(frame, message, [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75, [0, 0, 0], 1, cv2.LINE_AA)
        cv2.putText(frame, "Press 'g' to generate QR codes and 'q' to quit.", [10, 60], cv2.FONT_HERSHEY_DUPLEX, 0.75, [0, 0, 0], 1, cv2.LINE_AA)
        cv2.imshow("Scanning...", frame)
        cv2.setWindowProperty("Scanning...", cv2.WND_PROP_TOPMOST, 1)

        if len(data) > 0:
            return data

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            exit(0)

        elif key == ord('g'):
            cam.release()
            cv2.destroyAllWindows()
            generate_qr_codes()
            exit(0)


if __name__ == "__main__":
    print("Reading settings...")
    lines = read_file("resources/settings.txt")
    temps = []
    delay = -1
    room = -1

    try:
        for line in lines:
            if "QR Code" in line:
                temps.append(line)

            elif "Delay" in line:
                delay = int(line.split(":")[1].strip())

            elif "Room" in line:
                room = int(line.split(":")[1].strip())

            else:
                print("Unexpected value found in settings. Please review the file.")
                exit(1)

    except ValueError:
        print("Unexpected value for delay and/or room number in settings.txt. Please check and run again.")
        print("Exiting in 10 seconds (You can close this window)")
        sleep(10)
        exit(2)

    status_cells = {f"SF{room}-1": "G2", f"SF{room}-2": "H2", f"SF{room}-3": "I2", f"SF{room}-4": "J2", f"SF{room}-5": "K2", f"SF{room}-6": "L2"}
    status_rev = {"OUT": "IN", "IN": "OUT"}
    temps_dict = {f"student{i + 1}": val.split(":")[1].strip() for i, val in enumerate(temps)}
    date = datetime.today()
    print("Starting gspread client...")
    print("Opening camera. Smile!")
    chromebook = read_code("Please show chromebook")
    sleep(delay)
    name = read_code("Please show ID")
    cv2.destroyAllWindows()
    decrypt = read_json("resources/validation.json")

    print("Verifying inputs...")
    if name not in decrypt:
        print("QR code not recognized. Please get teacher to look into this.")
        exit(3)

    print("Starting gspread client...")
    client = gspread.service_account("resources/cbtracking-385301-ac9bc3a18813.json")
    sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")

    try:
        # Try this method to search for dates (hopefully faster).
        last_row = sheet.findall(f"{date.month}/{date.day}/{date.year}")[-1].row + 1

    except IndexError:
        # Use this method as a backup. Gets a list of all elements in a column and gets the length.
        last_row = len(sheet.col_values(1)) + 1

    print("Info good! Updating sheet...")
    name = decrypt[name]
    if name in temps_dict:
        name = temps_dict[name]

    try:
        sheet.update(status_cells[chromebook], status_rev[sheet.acell(status_cells[chromebook]).value])
        sheet.update(f"A{last_row}", chromebook)
        sheet.update(f"B{last_row}", sheet.acell(status_cells[chromebook]).value)
        sheet.update(f"C{last_row}", name)
        sheet.update(f"D{last_row}", f"{date.month}/{date.day}/{date.year}")
        sheet.update(f"E{last_row}", f"{date.hour}:{date.minute}:{date.second}")

    except Exception as e:
        print(f"Something went wrong. Please refer to exception log:\n{e}")
        print("Exiting in 10 seconds (You can close this window)")
        sleep(10)
        exit(4)

    print("Finished! Exiting in 5 seconds...")
    sleep(5)
