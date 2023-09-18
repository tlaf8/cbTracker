import json
import gspread
from json import JSONDecodeError


def obtain_auth(path: str) -> str:
    try:
        with open(path, "r") as auth:
            return auth.readlines()[0].strip()

    except FileNotFoundError:
        print("GSpread authentication could not be found. Please contact 21laforgth@gmail.com.")
        exit(6)


def get_statuses(sheet: gspread.Worksheet) -> dict:
    devices = sheet.col_values(7)[1::]
    statuses = sheet.col_values(8)[1::]
    return {val: statuses[row] for row, val in enumerate(devices)}


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
