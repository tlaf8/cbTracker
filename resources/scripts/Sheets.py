from .TermColor import TermColor
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


def update(entry: dict[str, str], sheet: Worksheet) -> None:
    """Update a Google Sheets document.

    Args:
        entry: The data entry to update.
        sheet: The Google Sheets document.
    """
    tc.print_ok("Updating sheet")

    status_cells: dict[str, Cell] = pull_statuses(sheet)

    # Grab last row + 1 from A to E, using A as search column
    data_lr: int = len(sheet.col_values(1))
    entry_cells: list[Cell] = sheet.range(f"A{data_lr + 1}:E{data_lr + 1}")

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

