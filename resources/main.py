import gspread
import cv2
from datetime import datetime
from time import sleep
from filelib import read_file


def read_code(message: str):
    cam = cv2.VideoCapture(0)
    reader = cv2.QRCodeDetector()

    while True:
        ret, frame = cam.read()
        data, _, _ = reader.detectAndDecode(frame)

        frame = cv2.flip(frame, 1)
        cv2.putText(frame, message, [10, 30], cv2.FONT_HERSHEY_DUPLEX, 1, [0, 0, 0], 1, cv2.LINE_AA)
        cv2.imshow("Haha funny", frame)

        if len(data) > 0:
            cam.release()
            cv2.destroyAllWindows()
            return data

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            exit(0)


lines = read_file("settings.txt")

try:
    # TODO: Find a better way to dynamically determine the amount of temp students. Maybe use a while loop and counter?
    temps = [entry.split(":")[1].strip() for entry in lines[0:15:]]
    delay = int(lines[15].split(":")[1].strip())
    room = int(lines[16].split(":")[1].strip())

except ValueError:
    print("Unexpected value for delay and/or room number in settings.txt. Please check and run again.")
    exit(1)

client = gspread.service_account("resources/cbtracking-385301-ac9bc3a18813.json")
sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")

status_cells = {f"SF{room}-1": "G2", f"SF{room}-2": "H2", f"SF{room}-3": "I2", f"SF{room}-4": "J2", f"SF{room}-5": "K2",f"SF{room}-6": "L2"}
status_rev = {"OUT": "IN", "IN": "OUT"}
temps_dict = {f"student{i + 1}": val for i, val in enumerate(temps)}
date = datetime.today()
chromebook = read_code("Please show chromebook")
sleep(delay)
name = read_code("Please show ID")

# TODO: Check to see if name matches any entry in validation.txt
if name not in read_file("resources/validation.txt"):
    print("Decoded name not recognized. Please get teacher to look into this.")
    exit(3)

try:
    # Try this method to search for dates (hopefully faster).
    last_row = sheet.findall(f"{date.month}/{date.day}/{date.year}")[-1].row + 1

except IndexError:
    # Use this method as a backup. Gets a list of all elements in a column and gets the length.
    last_row = len(sheet.col_values(1)) + 1

try:
    if name in temps_dict:
        name = temps_dict[name]

    sheet.update(status_cells[chromebook], status_rev[sheet.acell(status_cells[chromebook]).value])
    sheet.update(f"A{last_row}", chromebook)
    sheet.update(f"B{last_row}", sheet.acell(status_cells[chromebook]).value)
    sheet.update(f"C{last_row}", name)
    sheet.update(f"D{last_row}", f"{date.month}/{date.day}/{date.year}")
    sheet.update(f"E{last_row}", f"{date.hour}:{date.minute}:{date.second}")

except KeyError:
    print("Error writing to the sheet. Is the class room correct?")
    exit(4)
