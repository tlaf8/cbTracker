import json
from pwinput import pwinput
from resources.scripts.AWS import _pull
from resources.scripts.Logging import write_log
from resources.scripts.TermColor import TermColor
from resources.scripts.Exceptions import StopExecution

tc = TermColor()


def read(path: str, exit_on_error: bool = True) -> dict[str, str] | list[str] | None:
    """Reads data from a JSON file and handles potential errors.

    Args:
        path: The path to the JSON file to read.
        exit_on_error: Whether to exit the program on error (default: True).

    Returns:
        The contents of the JSON file as a dictionary, or an empty dictionary
        if the file is empty.
    """
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        tc.print_fail(f"File {path} could not be found. Check logs for more info")
        if "validation.json" in path or "api_key.json" in path:
            if input(
                    tc.format("[HELP]", "help") + " Sync local machine with version stored in cloud? (y/n) "
            ) in ["y", "yes"]:
                tc.print_help("Starting sync tool")
                aws_key: str = pwinput()
                _pull(aws_key)
                tc.print_ok("Downloaded keys. Please restart the program.")

        write_log()
        raise StopExecution

    except json.JSONDecodeError:
        if exit_on_error:
            tc.print_fail(f"File {path} invalid or empty. Check logs for more info")
            write_log()
            raise StopExecution

        else:
            tc.print_warning(f"File {path} is empty")
            return dict()


def write(path: str, data: dict[str, str]) -> None:
    """Writes data to a JSON file and handles potential errors.

    Args:
        path: The path to the JSON file to write to.
        data: The data to write as a dictionary.
    """
    with open(path, "w") as f:
        try:
            json.dump(data, f, indent=4)

        except (Exception,):
            tc.print_fail("Could not write json. Check logs for more info")
            write_log()
            raise StopExecution
