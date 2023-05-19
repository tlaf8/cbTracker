import gspread
import cv2
import json
import qrcode
import hashlib
from json.decoder import JSONDecodeError
from sys import exit
from base64 import b64decode
from datetime import datetime


def read_json(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        print("File could not be found.")
        input("Press ENTER to exit...")
        exit(5)

    except JSONDecodeError:
        print("File is empty. Generating QR codes. Please rerun the program.")
        generate_qr_codes()
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


def read_code(message: str) -> str:
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
            input("Finished! Press ENTER to exit...")
            exit(0)

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
        if name not in decrypt:
            print("QR code not recognized. Please get teacher to look into this.")
            continue

        print("Starting gspread client...")
        client = gspread.service_account_from_dict(json.loads(b64decode("eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6ImNidHJhY2tpbmctMzg1MzAxIiwicHJpdmF0ZV9rZXlfaWQiOiJhYzliYzNhMTg4MTM0OGM2MzUyMDA3YjE0NjI1NWM3ZGJkOGM2ZmIxIiwicHJpdmF0ZV9rZXkiOiItLS0tLUJFR0lOIFBSSVZBVEUgS0VZLS0tLS1cbk1JSUV1d0lCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktVd2dnU2hBZ0VBQW9JQkFRQ2FxMjA3WXU2NHFHdXlcbmR2a0U5RE5oRDBpdUtmWWJ3VkRhZVI4cTRUZGM4T1M0SmplbWw0QklJb1dsTHQ0c2ZsakxIQ01wNnR4SU1IMFdcblZoSG8xY0xYYlNwUXRZeDBxaFliek9sZzllT0F1ZFQ3VVI1cnhJMXNET0NaRUhLOUNadDZhKzlFd2NURU9CSlhcbkZvRGtGMzdxa01aNExSN2N0RC96RWJiSEF6WWR0Yjk3ZTk4U1Y0NHhlZURRQmhFK3FIRGJXd3QvWVUvNXQzbHJcbnFMSXhNSUc3T3IzOWRkVE5sU2RnQlE2VnFyVk5CeW81bGZBYjRUeDVSVmZqVXcxckhYeUZ1VXo5dWRFQWJUZFFcbm9iZkFyZG8wcEZWdzd3aXlSMUxiUHBpVGpITXBxVFY4aVl5RDdEL2VYeU1ENFFtNHdMMlZUNnozYSt1Y09NZmtcbi9KaWlnQ0tCQWdNQkFBRUNnZjhSOVg4M0poNW9oZDZjRXZMYTdwSHpkUnFVdGJEdytTeDRLemJ4T2lBZlpnNWRcbmtESW1PbjA5NTBVMUhsUTFkZTIvWjhjUHlNUmU0RnBjQU9COFA2ZS9ZczNjK3cvUGtESFAwNk9kcS9sVDYrV3dcbnBXWkU2aGtKNEtJSUNrdkw4R3pGVml6ZUZ1MjRDQWxLMHFudmNXZlpCbE9sQm1tMi9jaUxEcWpVdUt6YVZsbGNcbitIbUF1T3I2L0pVaXdMRWtSeUhoSGtGL0ZqZVA3NmRFcXI1dnE1Nk9RS0FKM0RxdmJ5aGVnZGlkUmpjVWozbWNcbmRlZHBMdktaL2ptZHVBaFc1R1ZxdU9kMng2aEZjQ21WZVRDY29FSTdJRUJnbEdhSTQ3LzlBYzVwbU1OQVdaM2dcbmRlVmNVZnRUdkFwRmZDNWdtYVB1eU9PNHRKNUU4dG5nS0x0cTNDRUNnWUVBekcvL29BZmQ2V2NrU3VsNVFVanlcbnB1K0lCdldtalVXRUFtSVFzQzZPeHowTkhqZi9McWhNV0owS3JXS3FCZGpHSzZKdG1ab3pWVnFHcjR0emdDSjRcbjloMUhaY0RoN1NHd2lSRGpFZTRndS90Zlh4QlVlWDlkazBRQmViZzBRR2lHV0NBV1VJMGJVcU1nZ2p0YXpBcnJcbmlnSk5ZOHRtbUphOFV2c3EzUUZ1TmxzQ2dZRUF3YTRMd2xIY2NocTMxeEhMNlExWlJvWlUvNFFPL3JSckJSVkJcbi8yNkdzdjlNNWZEb2FnaERvcDZObE4xMTZKWXZ1UFNUaVJteWtacExQVWI0Q0JCNXBQZGdDKzZxUDNpbno4SWpcbjFOSnJjeHhvbitOUVgxL3dpRkJ5dFNKMHM0d3MyUnluQ2g2NUtuZUxBQWxBYldMa2hUS1huY3BaRk1oK1RYR3hcbmNUdVMrVk1DZ1lBZGgwZksyNWdIOEdmamtobDdmb2ZkNk5jaStqUldUMllqMmZwREdGWnpITFJhV3dnMnV3UmNcbkFFTGNqRlcyaG5zSkxtcmFOdFdYVEg0THVQNnowVWJiZFpzc2JWRzBxSnNSRVNsYkc2UUt3dUlobndBMGxGcjFcbnZHcmlJK01ZTW9ERkZjMWpVUjVUTDFDd3Z0WDhoczlDbmRhRHhZdEtHdXVVcU1hbUtXQzc1UUtCZ0VpcTBaU2xcbi9Dei9vMHhaVEFWejBiUXBRSWpoOW5KUUpQc3lQNkhqeVR3dGw1K0taTmtyb3B6SUdsenBQb3oybEk4empJdGJcbkRlbWRWMjkxU2loVWJoK2NCUGhWSXFGUDFyNlhtN1FGQXZXY2loQzdTL09NM29WMmthTXVlMVRHV2lsWG04Q3JcblNGUUxxQ1pxVWpiNGJMOGcvVXZobU15NGNOTUR2a3k2eW1rckFvR0JBSkl0UkdpZ0tUV2huNkRnWWY5VmVpZWNcbkVabDFqRVM2SVM4V1ZlSG1sQzNqSEZvYnlqa2NUbVMyaEVGSjZQdGpYT3FmS0FmRGJFZndQL0k1V0h5RURCT2dcbkVHaXJWZk9hTVFJSzNBSSszMjdLWkQwQXZZS0tSc1R2UTZnYlpoSVUrdVdEcSt4dkFPamY3OEhha1FNV2ZkZGFcblRkdHVUM2pzTmJjN1FJWnRkSUszXG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLCJjbGllbnRfZW1haWwiOiJjYnRyYWNrZXJAY2J0cmFja2luZy0zODUzMDEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCJjbGllbnRfaWQiOiIxMDE5NDU3MzIxNTM2Mjk4NjMxMzgiLCJhdXRoX3VyaSI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwidG9rZW5fdXJpIjoiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLCJjbGllbnRfeDUwOV9jZXJ0X3VybCI6Imh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvY2J0cmFja2VyJTQwY2J0cmFja2luZy0zODUzMDEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20ifQ==")))
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
            sheet.update(f"D{last_row}", f"{'{:02d}'.format(date.month)}/{'{:02d}'.format(date.day)}/{'{:02d}'.format(date.year)}")
            sheet.update(f"E{last_row}", f"{date.hour}:{date.minute}:{date.second}")

        except Exception as e:
            print(f"Something went wrong. Exception:\n\t{type(e).__name__} --> {e}")
            input("Press ENTER to exit...")
            exit(4)
