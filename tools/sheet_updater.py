import gspread
import json
import sys
from base64 import b64decode
from time import sleep
from common import obtain_auth
from concurrent.futures import ThreadPoolExecutor


def update_sheet(cb_log: list) -> None:
    cb_id = cb_log[1]
    log_status = cb_log[2]
    student = cb_log[3]
    log_date = cb_log[4]
    log_time = cb_log[5]
    lr = cb_log[6]
    status = cb_log[7]

    try:
        sheet.update_cell(status[1], status[0], log_status)
        sheet.update_cell(lr, 1, cb_id)
        sheet.update_cell(lr, 2, log_status)
        sheet.update_cell(lr, 3, student)
        sheet.update_cell(lr, 4, log_date)
        sheet.update_cell(lr, 5, log_time)

    except Exception as e:
        print(f"Something went wrong. Exception:\n\t{type(e).__name__} --> {e}")
        exit(4)


if __name__ == '__main__':
    batch = [entry.split(" | ") for entry in b64decode(sys.argv[1]).decode().split(" -- ")]
    statuses = json.loads(b64decode(sys.argv[2]).decode())
    room = batch[0][0]
    status_cells = {f"SF{room}-{i}": f"8{i + 1}" for i in range(1, 7, 1)}
    status_cells.update({f"SFRED-{i}": f"8{i + 7}" for i in range(1, 33, 1)})

    # TODO: Update this to work with other classes if need be.
    #       Most likely need to update update_sheet() function
    #       in common to parse out room number in each entry
    client = gspread.service_account_from_dict(json.loads(b64decode(obtain_auth("./resources/gspread_auth.txt"))))
    sheet = client.open("Chromebook Tracker").worksheet(f"SF{room}")

    print("Updating sheet...")
    with ThreadPoolExecutor() as exe:
        for entry in batch:
            exe.submit(update_sheet, entry)
            sleep(0.25)

    print("Finished")
