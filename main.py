import gspread
import cv2
import json
import qrcode
import hashlib
from json.decoder import JSONDecodeError
from sys import exit
from datetime import datetime
from time import sleep


def read_json(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        print("File could not be found.")
        input("Press ENTER to exit...")
        exit(5)

    except JSONDecodeError:
        print("File is empty. Try creating QR codes.")
        input("Press ENTER to exit...")
        exit(6)


def read_file(path: str) -> list:
    try:
        with open(path, "r") as file:
            return [ln.rstrip() for ln in file.readlines() if ln != "\n" and "#" not in ln]

    except FileNotFoundError:
        print("File could not be found.")
        input("Press ENTER to exit...")
        exit(5)


def write_file(path: str, obj: dict):
    try:
        with open(path, "a") as file:
            json.dump(obj, file)

    except FileNotFoundError:
        print("File could not be found.")
        input("Press ENTER to exit...")
        exit(5)


def generate_qr_codes():
    ln = read_file(r"../../resources/classlist.txt")
    open("../../resources/validation.json", "w").close()

    codes = {}
    for entry in ln:
        temp = hashlib.sha256(f"{entry}paws".encode()).hexdigest()
        qrcode.make(temp).save(rf"../../resources/qr_codes/{entry}.png")
        codes[entry] = temp

    write_file(r"../../resources/validation.json", {v: k for k, v in codes.items()})


def read_code(message: str):
    cam = cv2.VideoCapture(0)
    reader = cv2.QRCodeDetector()

    while True:
        _, frame = cam.read()
        data, _, _ = reader.detectAndDecode(frame)

        frame = cv2.flip(frame, 1)
        cv2.putText(frame, message, [10, 30], cv2.FONT_HERSHEY_DUPLEX, 0.75, [0, 0, 0], 1, cv2.LINE_AA)
        cv2.putText(frame, "Press 'g' to generate QR codes and 'q' to quit.", [10, 60], cv2.FONT_HERSHEY_DUPLEX, 0.75,
                    [0, 0, 0], 1, cv2.LINE_AA)
        cv2.imshow("Scanning...", frame)
        cv2.setWindowProperty("Scanning...", cv2.WND_PROP_TOPMOST, 1)

        if len(data) > 0:
            return data

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            return "break"

        elif key == ord('g'):
            cam.release()
            cv2.destroyAllWindows()
            generate_qr_codes()
            print("Finished!")
            input("Press ENTER to exit...")
            exit(0)


if __name__ == "__main__":
    print("Reading settings...")
    lines = read_file("../../resources/settings.txt")
    temps = []
    room = -1

    try:
        for line in lines:
            if "QR Code" in line:
                temps.append(line)

            elif "Room" in line:
                room = int(line.split(":")[1].strip())

            else:
                print("Unexpected value found in settings. Please review the file.")
                input("Press ENTER to exit...")
                exit(1)

    except ValueError:
        print("Unexpected value for room number in settings.txt. Please check and run again.")
        input("Press ENTER to exit...")
        exit(2)

    status_cells = {f"SF{room}-1": "H2", f"SF{room}-2": "H3", f"SF{room}-3": "H4", f"SF{room}-4": "H5",
                    f"SF{room}-5": "H6", f"SF{room}-6": "H7"}
    status_rev = {"OUT": "IN", "IN": "OUT"}
    temps_dict = {f"student{i + 1}": val.split(":")[1].strip() for i, val in enumerate(temps)}
    decrypt = read_json("../../resources/validation.json")
    date = datetime.today()
    print("Opening camera. Smile!")

    while True:
        chromebook = read_code("Please show chromebook")
        name = read_code("Please show ID")
        cv2.destroyAllWindows()

        print("Verifying inputs...")
        if name == "break":
            break

        if name not in decrypt:
            print("QR code not recognized. Please get teacher to look into this.")
            continue

        print("Starting gspread client...")
        client = gspread.service_account_from_dict({
            'type': 'service_account', 'project_id': 'cbtracking-385301',
            'private_key_id': 'ac9bc3a1881348c6352007b146255c7dbd8c6fb1',
            'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQCaq207Yu64qGuy\ndvkE9DNhD0iuKfYbwVDaeR8q4Tdc8OS4Jjeml4BIIoWlLt4sfljLHCMp6txIMH0W\nVhHo1cLXbSpQtYx0qhYbzOlg9eOAudT7UR5rxI1sDOCZEHK9CZt6a+9EwcTEOBJX\nFoDkF37qkMZ4LR7ctD/zEbbHAzYdtb97e98SV44xeeDQBhE+qHDbWwt/YU/5t3lr\nqLIxMIG7Or39ddTNlSdgBQ6VqrVNByo5lfAb4Tx5RVfjUw1rHXyFuUz9udEAbTdQ\nobfArdo0pFVw7wiyR1LbPpiTjHMpqTV8iYyD7D/eXyMD4Qm4wL2VT6z3a+ucOMfk\n/JiigCKBAgMBAAECgf8R9X83Jh5ohd6cEvLa7pHzdRqUtbDw+Sx4KzbxOiAfZg5d\nkDImOn0950U1HlQ1de2/Z8cPyMRe4FpcAOB8P6e/Ys3c+w/PkDHP06Odq/lT6+Ww\npWZE6hkJ4KIICkvL8GzFVizeFu24CAlK0qnvcWfZBlOlBmm2/ciLDqjUuKzaVllc\n+HmAuOr6/JUiwLEkRyHhHkF/FjeP76dEqr5vq56OQKAJ3DqvbyhegdidRjcUj3mc\ndedpLvKZ/jmduAhW5GVquOd2x6hFcCmVeTCcoEI7IEBglGaI47/9Ac5pmMNAWZ3g\ndeVcUftTvApFfC5gmaPuyOO4tJ5E8tngKLtq3CECgYEAzG//oAfd6WckSul5QUjy\npu+IBvWmjUWEAmIQsC6Oxz0NHjf/LqhMWJ0KrWKqBdjGK6JtmZozVVqGr4tzgCJ4\n9h1HZcDh7SGwiRDjEe4gu/tfXxBUeX9dk0QBebg0QGiGWCAWUI0bUqMggjtazArr\nigJNY8tmmJa8Uvsq3QFuNlsCgYEAwa4LwlHcchq31xHL6Q1ZRoZU/4QO/rRrBRVB\n/26Gsv9M5fDoaghDop6NlN116JYvuPSTiRmykZpLPUb4CBB5pPdgC+6qP3inz8Ij\n1NJrcxxon+NQX1/wiFBytSJ0s4ws2RynCh65KneLAAlAbWLkhTKXncpZFMh+TXGx\ncTuS+VMCgYAdh0fK25gH8Gfjkhl7fofd6Nci+jRWT2Yj2fpDGFZzHLRaWwg2uwRc\nAELcjFW2hnsJLmraNtWXTH4LuP6z0UbbdZssbVG0qJsRESlbG6QKwuIhnwA0lFr1\nvGriI+MYMoDFFc1jUR5TL1CwvtX8hs9CndaDxYtKGuuUqMamKWC75QKBgEiq0ZSl\n/Cz/o0xZTAVz0bQpQIjh9nJQJPsyP6HjyTwtl5+KZNkropzIGlzpPoz2lI8zjItb\nDemdV291SihUbh+cBPhVIqFP1r6Xm7QFAvWcihC7S/OM3oV2kaMue1TGWilXm8Cr\nSFQLqCZqUjb4bL8g/UvhmMy4cNMDvky6ymkrAoGBAJItRGigKTWhn6DgYf9Veiec\nEZl1jES6IS8WVeHmlC3jHFobyjkcTmS2hEFJ6PtjXOqfKAfDbEfwP/I5WHyEDBOg\nEGirVfOaMQIK3AI+327KZD0AvYKKRsTvQ6gbZhIU+uWDq+xvAOjf78HakQMWfdda\nTdtuT3jsNbc7QIZtdIK3\n-----END PRIVATE KEY-----\n',
            'client_email': 'cbtracker@cbtracking-385301.iam.gserviceaccount.com',
            'client_id': '101945732153629863138',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/cbtracker%40cbtracking-385301.iam.gserviceaccount.com'
        })
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
            print(f"Something went wrong. Exception:\n\t{type(e).__name__} --> {e}")
            input("Press ENTER to exit...")
            exit(4)

    input("Finished! Press ENTER to exit...")
    exit(0)
