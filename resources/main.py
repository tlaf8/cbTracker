import gspread
import cv2
from datetime import datetime
from time import sleep


def read_code(message):
    cam = cv2.VideoCapture(0)
    reader = cv2.QRCodeDetector()

    while True:
        ret, frame = cam.read()
        data, bbox, straight_qrcode = reader.detectAndDecode(frame)

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


with open("settings.txt", "r") as settings:
    lines = [line.rstrip() for line in settings if line != "\n"]

try:
    temps = [entry.split(":")[1].strip() for entry in lines[0:15:]]
    delay = int(lines[15].split(":")[1].strip())
    room = int(lines[16].split(":")[1].strip())

except ValueError:
    print("Unexpected value for delay and/or room number in settings.txt. Please check again and run.")
    exit(1)

temps_dict = {f"student{i + 1}": val for i, val in enumerate(temps)}

client = gspread.service_account("resources\\cbtracking-385301-ac9bc3a18813.json")
sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")

status_cells = {f"SF{room}-1": "G2", f"SF{room}-2": "H2", f"SF{room}-3": "I2", f"SF{room}-4": "J2", f"SF{room}-5": "K2", f"SF{room}-6": "L2"}
status_rev = {"OUT": "IN", "IN": "OUT"}

date = datetime.today()

chromebook = read_code("Please show chromebook")
sleep(delay)
name = read_code("Please show ID")

try:
    last_row = sheet.findall(f"{date.month}/{date.day}/{date.year}")[-1].row + 1

except IndexError:
    print("Empty spreadsheet. Running first row")
    last_row = 2

try:
    sheet.update(status_cells[chromebook], status_rev[sheet.acell(status_cells[chromebook]).value])
    sheet.update(f"A{last_row}", chromebook)
    sheet.update(f"B{last_row}", sheet.acell(status_cells[chromebook]).value)

    if name in temps_dict:
        name = temps_dict[name]

    sheet.update(f"C{last_row}", name)
    sheet.update(f"D{last_row}", f"{date.month}/{date.day}/{date.year}")
    sheet.update(f"E{last_row}", f"{date.hour}:{date.minute}:{date.second}")

except KeyError:
    print("Error writing to the sheet. Is the class room correct?")
