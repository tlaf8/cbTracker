import os
import json
import time
import cv2
import base64
import requests
import traceback
import qrcode as qr
from hashlib import sha256
from pwinput import pwinput
from PIL import Image, ImageDraw, ImageFont


class TC:
    """
    A class for text coloring and formatting with predefined color codes.

    Attributes:
        ok (str): ANSI escape code for green messages.
        fail (str): ANSI escape code for red messages.
        help (str): ANSI escape code for blue messages.
        warning (str): ANSI escape code for yellow messages.
        end (str): ANSI escape code for ending text formatting.

    Methods:
        format(txt: str, category: str) -> str:
            Format the given text with the appropriate ANSI escape code based on the specified category.

        print_ok(msg: str) -> None:
            Print a message in green.

        print_fail(msg: str) -> None:
            Print a message in red.

        print_help(msg: str) -> None:
            Print a message in blue.

        print_warning(msg: str) -> None:
            Print a message in yellow.

        print_fatal(msg: str) -> None:
            Print a message in red indicating fatal errors.
    """

    def __init__(self) -> None:
        """
        Initialize TC class with predefined ANSI escape codes for different message categories.
        """
        self.ok = '\033[92m'
        self.fail = '\033[91m'
        self.help = '\033[36m'
        self.warning = '\033[93m'
        self.end = '\033[0m'

    def format(self, txt: str, category: str) -> str:
        """
        Format the given text with the appropriate ANSI escape code based on the specified category.

        Args:
            txt (str): The text to be formatted.
            category (str): The category of the message. Can be one of 'ok', 'fail', 'help', 'warning', or 'fatal'.

        Returns:
            str: The formatted text with the appropriate ANSI escape code.
        """
        match category:
            case "ok":
                return f"{self.ok}{txt}{self.end}"

            case "fail":
                return f"{self.fail}{txt}{self.end}"

            case "help":
                return f"{self.help}{txt}{self.end}"

            case "warning":
                return f"{self.warning}{txt}{self.end}"

            case "fatal":
                return f"{self.fail}{txt}{self.end}"

            case _:
                return f"{self.ok}{txt}{self.end}"

    def print_ok(self, msg: str) -> None:
        """
        Print a message with an OK indicator.

        Args:
            msg (str): The message to be printed.
        """
        print(f"{self.ok}[INFO]{self.end}\t{msg}")

    def print_fail(self, msg: str) -> None:
        """
        Print a message with a FAIL indicator.

        Args:
            msg (str): The message to be printed.
        """
        print(f"{self.fail}[FAIL]{self.end}\t{msg}")

    def print_help(self, msg: str) -> None:
        """
        Print a message with a HELP indicator.

        Args:
            msg (str): The message to be printed.
        """
        print(f"{self.help}[HELP]{self.end}\t{msg}")

    def print_warning(self, msg: str) -> None:
        """
        Print a message with a WARNING indicator.

        Args:
            msg (str): The message to be printed.
        """
        print(f"{self.warning}[WARN]{self.end}\t{msg}")

    def print_fatal(self, msg: str) -> None:
        """
        Print a message with a FATAL indicator.

        Args:
            msg (str): The message to be printed.
        """
        print(f"{self.fail}[FATAL]{self.end}\t{msg}")


def write_log() -> None:
    """Write traceback logs to a file."""
    try:
        with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
            traceback.print_exc(file=log)

        exit(1)

    except FileNotFoundError:
        os.mkdir("logs")
        write_log()


def read_txt(path: str) -> tuple[list[str], list[str]]:
    """Read data from a text file.

    Args:
        path (str): The path to the text file.

    Returns:
        tuple: A tuple containing two lists - lines not starting with '#' and lines starting with '#'.
    """
    with open(path, 'r') as file_in:
        return [line for line in file_in if line[0] != '#'], [line for line in file_in if line[0] == '#']


def read_json(path: str, exit_on_err=True) -> dict[str: str] | list:
    """Read JSON data from a file.

    Args:
        path (str): The path to the JSON file.
        exit_on_err (bool, optional): Whether to exit the program on error. Defaults to True.

    Returns:
        dict | list: The JSON data read from the file.
    """
    tc = TC()
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        tc.print_fail(f"File {path} could not be found. Check logs for more info")
        if "validation.json" in path or "api_key.json" in path:
            if input(tc.print_help(f"Looks like {path} is missing. Download it? (y/n) ")).lower() == "y":
                sync_local(pwinput())
                tc.print_ok("Files downloaded successfully")
                tc.print_ok("Exiting in 5")
                time.sleep(5)
                exit(0)

            else:
                exit(0)

        else:
            write_log()
            exit(1)

    except json.JSONDecodeError:
        if exit_on_err:
            tc.print_fail(f"File {path} invalid or empty. Check logs for more info")
            write_log()
            exit(1)

        else:
            tc.print_warning(f"File {path} is empty")
            return []


def write_json(path: str, data: dict) -> None:
    """Write JSON data to a file.

    Args:
        path (str): The path to the JSON file.
        data (dict): The data to be written.
    """
    tc = TC()
    with open(path, "w") as f:
        try:
            json.dump(data, f, indent=4)

        except (Exception,):
            tc.print_fail("Could not write json. Check logs for more info")
            write_log()
            exit(1)


def sync_local(pwd: str) -> None:
    """Synchronize local data with AWS.

    Args:
        pwd (str): The password for authentication.
    """
    tc = TC()
    returned = requests.post("https://tryobgwrhsrnbyq5re77znzxry0brhfc.lambda-url.ca-central-1.on.aws/",
                             data={
                                 "pass": sha256(pwd.encode()).hexdigest()
                             }
                             ).content.decode("utf-8")

    if returned == "Unauthorized: Bad password":
        tc.print_fail(returned)
        exit(1)

    returned = json.loads(returned)
    api_key = json.loads(returned["api_key"])
    validation = json.loads(returned["validation"])

    write_json("resources/data/api_key.json", api_key)
    write_json("resources/data/validation.json", validation)


def update_sheet(entry, sheet) -> None:
    """Update a Google Sheets document.

    Args:
        entry: The data entry to update.
        sheet: The Google Sheets document.
    """
    tc = TC()
    tc.print_ok("Updating sheet")

    # Go from H2 to the end of data in column H
    status_lr = len(sheet.col_values(8))
    status_cells = dict(zip(
        # Device name (Column G) ------------maps to------------> Device status (Column H)
        [name.value for name in sheet.range(f"G2:G{status_lr}")], sheet.range(f"H2:H{status_lr}")
    ))

    # Grab last row + 1 from A to E, using A as search column
    data_lr = len(sheet.col_values(1))
    entry_cells = sheet.range(f"A{data_lr + 1}:E{data_lr + 1}")

    # Set status cell value
    status_cells[entry["device"]].value = entry["action"]

    # Set values to data given in entry accordingly
    entry_cells[0].value = entry["device"]
    entry_cells[1].value = entry["action"]
    entry_cells[2].value = entry["student"]
    entry_cells[3].value = entry["date"]
    entry_cells[4].value = entry["time"]

    # Update the cb_sheet with new values
    sheet.update_cells(list(status_cells.values()) + entry_cells)

    tc.print_ok("Finished updating sheet")


def show_img(img_path: str, msg: str = "") -> None:
    """Show processing image with a message.

    Args:
        img_path (str): The path to the image file.
        msg (str, optional): The message to display. Defaults to "".
    """
    img = cv2.putText(img=cv2.imread(img_path),
                      text=msg,
                      org=[10, 30],
                      fontFace=cv2.FONT_HERSHEY_DUPLEX,
                      fontScale=0.75,
                      color=[0, 0, 0],
                      thickness=1,
                      lineType=cv2.LINE_AA)
    cv2.imshow("Scanner", img)


def read_code(cam: cv2.VideoCapture,
              decoder: cv2.QRCodeDetector,
              msg: str,
              hash_dict: dict,
              status_dict: dict,
              expecting: str) -> tuple[str, str]:
    """Read QR codes from camera input.

    Args:
        cam (cv2.VideoCapture): The camera object.
        decoder (cv2.QRCodeDetector): The QR code decoder object.
        msg (str): The message to display.
        hash_dict (dict): Dictionary containing hashed IDs.
        status_dict (dict): Dictionary containing status values.
        expecting (str): The expected data type.

    Returns:
        tuple[str, str]: A tuple containing the obtained data and action.
    """
    tc = TC()
    settings: dict = read_json("resources/data/settings.json")
    status_flip = {"IN": "OUT", "OUT": "IN"}
    while True:
        _, raw_frame = cam.read()
        raw_result, _, _ = decoder.detectAndDecode(raw_frame)
        if raw_frame is None:
            cv2.destroyAllWindows()
            cam.release()
            tc.print_fail("Could not read camera")
            write_log()

        else:
            # Camera read, but no qr codes detected
            if raw_result == "":
                frame = cv2.flip(raw_frame, 1)

                # Window setup
                cv2.namedWindow("Scanner", flags=cv2.WINDOW_GUI_NORMAL)
                cv2.resizeWindow("Scanner", settings["window x"], settings["window y"])
                cv2.putText(img=frame,
                            text=msg,
                            org=[10, 30],
                            fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.75,
                            color=[0, 0, 0],
                            thickness=1,
                            lineType=cv2.LINE_AA)
                cv2.putText(img=frame,
                            text="Press 'q' to quit",
                            org=[10, 60],
                            fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.75,
                            color=[0, 0, 0],
                            thickness=1,
                            lineType=cv2.LINE_AA)

                cv2.imshow("Scanner", frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    cam.release()
                    tc.print_ok("Exiting")
                    exit(0)

                elif key == ord('s'):
                    cv2.destroyAllWindows()
                    cam.release()
                    if input("Sync local machine with AWS? (y/n) ").lower() == "y":
                        aws_key = pwinput()
                        sync_local(aws_key)
                        print("Finished syncing local machine")

                    if input("Sync AWS with local machine? (y/n) ").lower() == "y":
                        aws_key = pwinput()
                        upload_data(
                            read_json("resources/data/validation.json", exit_on_err=True),
                            "validation",
                            aws_key
                        )
                        upload_data(
                            read_json("resources/data/api_key.json", exit_on_err=True),
                            "apikey",
                            aws_key
                        )
                        print("Finished syncing AWS")

                elif key == ord('n'):
                    cv2.destroyAllWindows()
                    cam.release()
                    create_qr_codes(
                        "resources/qr_codes/output",
                        fuzz=pwinput(f"Fuzzer for convolution (Ex. John{tc.format('fuzz', 'fail')}Doe): ")
                    )

            else:
                tc.print_ok(f"Read value: {raw_result}")
                if raw_result in hash_dict:  # Student ID was scanned
                    show_img("resources/img/scan_img.png",
                             f"Obtained: {(decrypt := hash_dict[raw_result])}"
                             )
                    cv2.waitKey(500)

                    if expecting == "student":
                        return decrypt, ""  # Return empty string for consistency

                    else:
                        show_img("resources/img/loading.png", "Expected a device")
                        cam.release()
                        cv2.waitKey(3000)

                elif raw_result in status_dict:  # Device was scanned
                    action = status_flip[status_dict[result := raw_result].value]
                    show_img("resources/img/scan_img.png", f"Obtained: {result}")
                    cv2.waitKey(500)

                    if expecting == "device":
                        return result, action

                    else:
                        show_img("resources/img/loading.png", "Expected an ID")
                        cam.release()
                        cv2.waitKey(3000)


def upload_data(data: dict, kind: str, pwd: str) -> str:
    """Upload data to AWS.

    Args:
        data (dict): The data to upload.
        kind (str): The type of data.
        pwd (str): The password for authentication.

    Returns:
        str: Response message.
    """
    params = {
        "pass": sha256(pwd.encode()).hexdigest(),
        "kind": kind,
        "data": base64.urlsafe_b64encode(json.dumps(data).encode())
    }

    resp = requests.post("https://i5nqbfht5a6v4epzr5anistot40qkyaz.lambda-url.ca-central-1.on.aws/",
                         data=params
                         )
    return resp.content.decode("utf-8")


def img_draw_txt(path: str, filename: str):
    font = ImageFont.truetype("resources/data/RobotoMono-Regular.ttf", size=16)
    img = Image.open(f"{path}/{filename}.png")
    printer = ImageDraw.Draw(img)
    printer.text((img.width / 2 - font.getlength(filename) / 2, img.height - 30), filename, font=font)
    img.save(f"{path}/{filename}.png")


def create_qr_codes(path_out: str, fuzz: str = None, from_file=False) -> None:
    """Create QR codes.

    Args:
        path_out (str): The output path for the QR codes.
        fuzz (str, optional): Fuzz string for hashing. Defaults to None.
        from_file (bool, optional): Whether to read names from a file. Defaults to False.
    """

    # DO NOT REMOVE! Code created courtesy of developer and princess Lily
    # help(code)

    if from_file is True:
        names, comments = read_txt("resources/qr_codes/creation_list.txt")
        open("resources/qr_codes/creation_list.txt", 'w').close()
        with open("resources/qr_codes/creation_list.txt", 'w') as creation_list:
            creation_list.writelines(comments)

    names: dict = {}
    print("Enter nothing when finished.")
    while True:
        if (name := input("Enter full name of student/device: ")) != "":
            if len(name.split(" ")) < 2:
                if input("Only one name found. Is this a device? (y/n) ").lower() == "y":
                    names[" ".join([i.strip() for i in name.split()])] = "no-encrypt"

            else:
                names[" ".join([i.strip() for i in name.split()])] = "encrypt"

            continue
        break

    print("Creating QR codes for the following names:")
    for name, proc in names.items():
        print(f"  --> {name:<20} ({proc})")

    if input("Continue? (y/n) ").lower() == 'y':
        validation_json = read_json("resources/data/validation.json", exit_on_err=True)
        for entry, encrypt in names.items():
            stripped = entry.strip()

            if encrypt == "encrypt":
                try:
                    qr.make(
                        data := sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                    ).save(f"{path_out}/{stripped}.png")
                    img_draw_txt(path_out, stripped)

                except FileNotFoundError:
                    print("Path invalid. Defaulting")
                    qr.make(
                        data := sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                    ).save(f"resources/qr_codes/output/{stripped}.png")
                    img_draw_txt(f"resources/qr_codes/output", stripped)

                if data in validation_json:
                    print("Name already exists. Regenerating QR code")
                    qr.make(data).save(f"{path_out}/{stripped}.png")
                    img_draw_txt(path_out, stripped)
                    continue

                validation_json[data] = stripped
                write_json("resources/data/validation.json", validation_json)

            else:
                qr.make(stripped).save(f"{path_out}/{stripped}.png")
                img_draw_txt(path_out, stripped)
