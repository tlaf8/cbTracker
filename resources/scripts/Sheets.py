from resources.scripts.TermColor import TermColor
from gspread import Worksheet, Cell

tc = TermColor()


def pull_statuses(sheet: Worksheet) -> dict[str, Cell]:
    """Obtains the status columns from the given worksheet.

    Args:
        sheet: gspread worksheet to pull from.
    """
    statuses: dict[str, Cell] = {}
    last_row: int = len(sheet.col_values(7))
    statuses.update(
        zip(
            # Device name (Column G) ------------maps to-----------> Device status (Column H)
            [name.value for name in sheet.range(f"G2:G{last_row}")], sheet.range(f"H2:H{last_row}")
        )
    )

    return statuses


def update(entries: list[dict[str, str]], sheets: dict[str, Worksheet]) -> None:
    """Update a Google Sheets document.

    Args:
        entries: The data entry to update.
        sheets: The Google Sheets document.
    """
    tc.print_ok("Updating sheet")

    # Separate data format to sort the scans in the queue
    entry_groups = {
        "chromebook": [],
        "calculator": [],
        "religion": [],
        "science": [],
        # "testing": []
    }

    # Sort out the entries
    for entry in entries:
        if "CALC" in entry["device"]:
            entry_groups["calculator"].append(entry)
        elif "REL7" in entry["device"]:
            entry_groups["religion"].append(entry)
        elif "SCI8" in entry["device"]:
            entry_groups["science"].append(entry)
        else:
            entry_groups["chromebook"].append(entry)
            # entry_groups["testing"].append(entry)

    # Run through each of the sheets and push updates for each if there are any updates
    for s, e in entry_groups.items():
        if len(e) == 0:
            continue

        sheet = sheets[s]
        status_cells: dict[str, Cell] = pull_statuses(sheet)

        # Grab last row + 1 from A to E, using A as search column
        data_lr: int = len(sheet.col_values(1))

        # Create an empty list to hold the cell objects
        cells_to_update: list[Cell] = []
        for i, entry in enumerate(e):
            if entry["device"] in status_cells:
                status_cells[entry["device"]].value = entry["action"]
                cells_to_update.append(status_cells[entry["device"]])

            entry_cells = sheet.range(f"A{data_lr + i + 1}:E{data_lr + i + 1}")
            entry_cells[0].value = entry["device"]
            entry_cells[1].value = entry["action"]
            entry_cells[2].value = entry["student"]
            entry_cells[3].value = entry["date"]
            entry_cells[4].value = entry["time"]
            cells_to_update.extend(entry_cells)

            sheet.update_cells(cells_to_update)

    tc.print_ok("Finished updating sheet")
