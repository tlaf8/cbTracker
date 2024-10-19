import os
import time
import traceback


def write_log() -> None:
    """Writes the current traceback to a timestamped log file.

    Creates the "logs" directory if it doesn't exist, and terminates the program
    after logging to prevent further errors.
    """
    try:
        with open(f"logs/{time.strftime('%Y-%m-%d_%H%M%S')}_log.txt", "w+") as log:
            traceback.print_exc(file=log)

    except FileNotFoundError:
        os.mkdir("logs")
        write_log()
