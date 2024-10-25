import cv2
import gspread
import numpy as np
import threading as th
from tqdm import tqdm
from time import sleep
from datetime import datetime
from resources.scripts.FileIO import read
from resources.scripts.Logging import write_log
from resources.scripts.TermColor import TermColor
from resources.scripts.QRProcessor import QRProcessor
from resources.scripts.Sheets import update, pull_statuses
from gspread import Cell, Worksheet, Spreadsheet, service_account
from resources.scripts.Exceptions import BadOrderException, UnknownQRCodeException, StopExecution

timer = None

def update_sheet_in_thread(ent, shts):
    """
    Updates the sheet if there are entries and restarts the timer.

    Checks if there are any entries in the given list. If there are,
    it triggers the update function to update the given sheet with updates in the queue.
    After the update, it clears the queue and restarts the timer for the next update.

    Args:
        ent (list[dict[str, str]]): A list of entries to be updated on the sheet.
        shts (dict[str, Worksheet]): The sheet object that needs to be updated.
    """
    if len(ent) == 0:
        tc.print_ok("No entries. Skipping update.")
    else:
        update(ent, shts)
        ent.clear()

    # Restart the timer after the update is done
    start_timer(ent, shts)


def start_timer(ent, shts):
    """
    Starts a timer to trigger the update every 100 seconds.

    Sets a timer that will call `update_sheet_in_thread` after 100 seconds.
    The timer runs in a separate thread, allowing the rest of the program to continue
    execution while waiting for the next update.

    Args:
        ent (list[dict[str, str]]): A list of entries to be passed to the update function.
        shts (dict[str, Worksheet]): The sheet object to be updated when the timer triggers.
    """
    global timer
    if isinstance(timer, th.Timer) and timer.is_alive():
        timer.cancel()

    timer = th.Timer(100, update_sheet_in_thread, args=(ent, shts))
    timer.start()


def stop_timer():
    """
    Cancels the running timer if it's active.
    """
    global timer
    if isinstance(timer, th.Timer) and timer.is_alive():
        timer.cancel()


if __name__ == "__main__":
    tc: TermColor = TermColor()
    tc.print_ok("Setting up")

    # variables
    entry: dict[str, str] = {}
    devices: dict[str, Cell] = {}

    # file i/o and images
    try:
        decrypt: dict[str, str] = read("resources/data/validation.json")
        settings: dict[str, str] = read("resources/data/settings.json")
        updating: np.ndarray = cv2.imread("resources/img/updating.png")

    except StopExecution:
        exit(-1)

    # gspread setup
    client: service_account = gspread.service_account_from_dict(read("resources/data/api_key.json"))

    main_sheet: Spreadsheet = client.open("Chromebook Tracker")
    sheets: dict[str, Worksheet] = {
        "chromebook": main_sheet.worksheet(settings["chromebook sheet"]),
        "calculator": main_sheet.worksheet(settings["calculator sheet"]),
        "religion": main_sheet.worksheet(settings["religion sheet"]),
        "science": main_sheet.worksheet(settings["science sheet"]),
        # "testing": main_sheet.worksheet("testing"),
    }

    # Update statuses of all rentals
    for s in tqdm(
            sheets.values(),
            unit=" sheets",
            desc="Pulling sheet data",
            colour="white",
            dynamic_ncols=True,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [Elapsed: {elapsed}]"
    ):
        devices.update(pull_statuses(s))

    # cv2
    qr_proc: QRProcessor = QRProcessor(decrypt)

    entries: list[dict[str, str]] = []

    # Start the initial timer
    start_timer(entries, sheets)

    while True:
        try:
            device: str
            action: str
            student: str

            # Scan QR codes for ID and rental
            device, action = qr_proc.process_code(qr_proc.read_code("Show Rental", [*devices]), devices, "rental")
            student = qr_proc.process_code(qr_proc.read_code("Show ID", [*devices]), devices, "student")

            # Wait so user can pull old QR code out of the way
            cv2.waitKey(500)
            cv2.imshow("Scanner", updating)
            cv2.waitKey(1)

            # Add updates to queue
            # Look at using file for queue to preserve data in case crash
            entry = {}
            current_time: datetime = datetime.now()
            entry["action"] = action
            entry["device"] = device
            entry["date"] = f"{current_time.day}/{current_time.month}/{current_time.year}"
            entry["student"] = student
            entry["time"] = f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}"
            devices[device].value = {"IN": "OUT", "OUT": "IN"}[action]
            entries.append(entry)

        # Handle OpenCV errors (if any)
        except cv2.error:
            tc.print_warning("OpenCV threw some errors, can likely ignore")

        # Handle custom exceptions
        except BadOrderException:
            continue

        except UnknownQRCodeException:
            continue

        # Handle reaching of API usage limit
        except gspread.exceptions.APIError:
            tc.print_fatal("API limit reached. Give me 100 seconds to cool down...")
            sleep(100)
            tc.print_ok("Done cooling down. Restart the program now.")

        # Stop the timer before exiting
        except StopExecution:
            stop_timer()
            break

        # Catch any other exceptions
        except (Exception,):
            cv2.destroyAllWindows()
            tc.print_fatal("Unknown error occurred. See logs for more details.")
            write_log()
            break
