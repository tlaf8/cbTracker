import json
from .AWS import handle_sync
from .Logging import write_log
from .TermColor import TermColor
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
            if input(tc.print_help("Sync local machine with version stored in cloud? (y/n) ")) in ["y", "yes"]:
                tc.print_help("Starting sync tool")
                handle_sync()

        write_log()
        exit(1)

    except json.JSONDecodeError:
        if exit_on_error:
            tc.print_fail(f"File {path} invalid or empty. Check logs for more info")
            write_log()
            exit(1)

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
            exit(1)
