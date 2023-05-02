def read_file(path: str):
    try:
        with open(path, "r") as file:
            return [line.rstrip() for line in file if line != "\n" and "#" not in line]

    except FileNotFoundError:
        print("File could not be found.")
        exit(2)


def write_file(path: str, iterable: list):
    try:
        with open(path, "a") as file:
            for entry in iterable:
                file.write(entry + "\n")

    except FileNotFoundError:
        print("File could not be found.")
        exit(2)
