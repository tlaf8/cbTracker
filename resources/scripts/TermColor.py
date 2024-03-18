class TermColor:
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
        Initialize TermColor class with predefined ANSI escape codes for different message categories.
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
