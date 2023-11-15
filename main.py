from tools import *
from threading import Timer
from datetime import datetime
from colouring import TC


if __name__ == "__main__":
    break_flag = 0
    decoder = cv2.QRCodeDetector()
    proc_img = cv2.imread("./resources/img/scan_img.jpg")
    unhash: dict = read_json("./resources/data/validation.json")
    settings: dict = read_json("./resources/data/settings.json")
    chromebooks: dict = read_json("./resources/data/status.json")
    batch: dict | list = read_json("./resources/data/batch.json", exit_on_err=False)
    update_queue = Timer(settings["update"], update_sheet, args=[settings["update"]])
    update_queue.daemon = True
    update_queue.start()
    print(f"{TC.OKGREEN}[INFO]{TC.ENDC}\tTimer started")
    while True:
        try:
            cam = cv2.VideoCapture(0)
            cb, action = read_code(cam, decoder, "Show Chromebook", unhash, chromebooks, proc_img, settings["update"])
            cam.release()

            cam = cv2.VideoCapture(0)
            student = read_code(cam, decoder, "Show ID", unhash, chromebooks, proc_img, settings["update"])
            cam.release()

            current_time = datetime.now()
            batch.append({
                "action": action,
                "chromebook": cb,
                "date": f"{current_time.day}/{current_time.month}/{current_time.year}",
                "student": student,
                "time": f"{current_time.hour}:{current_time.minute}:{current_time.second}"
            })

            write_json("./resources/data/batch.json", batch)

        except cv2.error as err:
            pass

        except Exception as err:
            print(f"[ERROR]\t{err}")
