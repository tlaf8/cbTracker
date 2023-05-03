import json


def read_json(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        print("File could not be found.")
        exit(5)


def read_file(path: str) -> list:
    try:
        with open(path, "r") as file:
            return [line.rstrip() for line in file.readlines() if line != "\n" and line != "#"]

    except FileNotFoundError:
        print("File could not be found.")
        exit(5)


def write_file(path: str, obj: dict):
    try:
        with open(path, "a") as file:
            json.dump(obj, file)

    except FileNotFoundError:
        print("File could not be found.")
        exit(5)
