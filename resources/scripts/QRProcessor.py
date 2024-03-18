import cv2
import numpy as np
from .FileIO import read, write
from .TermColor import TermColor
from .Logging import write_log
from .AWS import handle_sync
import qrcode as qr
from hashlib import sha256
from pwinput import pwinput
from .ImageTools import add_text, add_text_f
from .Exceptions import BadOrderException, UnknownQRCodeException
tc = TermColor()


class QRProcessor:
    def __init__(self, hash_dict: dict[str, str], status_dict: dict[str, any]):
        """Initializes the QR processor with dictionaries for lookups and camera resources.

        Args:
            hash_dict: A dictionary containing hashed QR code data for students.
            status_dict: A dictionary containing device statuses.
        """
        self.hash_dict: dict[str, str] = hash_dict
        self.status_dict: dict[str, any] = status_dict
        self.decoder: cv2.QRCodeDetector = cv2.QRCodeDetector()
        self.loading: np.ndarray = cv2.imread("resources/img/loading.png")
        self.scan_img: np.ndarray = cv2.imread("resources/img/scan_img.png")

    def read_code(self, message: str) -> str:
        """Reads a QR code from the camera.

        Args:
            message: A message to display on the camera preview.

        Returns:
            The decoded QR code data if successful, otherwise raises exceptions.
        """
        cam: cv2.VideoCapture = cv2.VideoCapture(0)
        while True:
            raw_frame: np.ndarray
            _, raw_frame = cam.read()

            if raw_frame is None:
                cv2.destroyAllWindows()
                cam.release()
                tc.print_fail("Could not read camera")
                write_log()

            raw_result: str
            raw_result, _, _ = self.decoder.detectAndDecode(raw_frame)
            if raw_result != "":
                if raw_result not in self.status_dict.keys() and raw_result not in self.hash_dict.keys():
                    badin: np.ndarray = add_text(self.loading.copy(), "Unrecognized QR Code", [10, 30])
                    cv2.imshow("Scanner", badin)
                    cv2.waitKey(3000)
                    raise UnknownQRCodeException

                tc.print_ok(f"Read value: {raw_result}")
                cam.release()
                return raw_result

            frame: np.ndarray = cv2.flip(raw_frame, 1)
            frame = add_text(frame, message, [10, 30])
            frame = add_text(frame, "Press 'q' to quit", [10, 60])
            cv2.namedWindow("Scanner", flags=cv2.WINDOW_GUI_NORMAL)
            cv2.imshow("Scanner", frame)

            # Handle key presses
            key: int = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                cam.release()
                tc.print_ok("Exiting")
                exit(0)

            elif key == ord('s'):
                cv2.destroyAllWindows()
                handle_sync()

            elif key == ord('n'):
                cv2.destroyAllWindows()
                self.create_qr_codes(
                    "resources/qr_codes/output",
                    fuzz=pwinput(f"Fuzzer for convolution (Ex. John{tc.format('fuzz', 'fail')}Doe): ")
                )

    def process_code(self, data: str, expecting: str) -> str | tuple[str, str]:
        """Processes the decoded QR code data based on expectations.

        Args:
            data: The decoded QR code data.
            expecting: The expected type of data ("student" or "device").

        Returns:
            The processed value (student ID or device status), or raises exceptions.
        """
        if data in self.hash_dict:
            obtained: np.ndarray = add_text(self.scan_img.copy(), f"Obtained: {(self.hash_dict[data])}", [10, 30])
            cv2.imshow("Scanner", obtained)
            cv2.waitKey(500)

            if expecting == "student":
                return self.hash_dict[data]

            else:
                expected: np.ndarray = add_text(self.loading.copy(), "Expected a device", [10, 30])
                cv2.imshow("Scanner", expected)
                cv2.waitKey(3000)
                raise BadOrderException

        elif data in self.status_dict:
            action: str = {"IN": "OUT", "OUT": "IN"}[self.status_dict[data].value]  # lol

            obtained: np.ndarray = add_text(self.scan_img.copy(), f"Obtained: {data}", [10, 30])
            cv2.imshow("Scanner", obtained)
            cv2.waitKey(500)

            if expecting == "device":
                return data, action

            else:
                expected: np.ndarray = add_text(self.loading.copy(), "Expected an ID", [10, 30])
                cv2.imshow("Scanner", expected)
                cv2.waitKey(3000)
                raise BadOrderException

    @staticmethod
    def create_qr_codes(path_out: str, fuzz: str = None) -> None:
        """Creates QR codes for student/device names and optionally encrypts them.

        Args:
            path_out: The output path to save the QR code images.
            fuzz: An optional string to add a fuzzing factor for encryption.
        """
        names: dict[str, str] = {}
        tc.print_help("Enter nothing when finished.")

        while (name := input("Enter full name of student/device: ")) != "":
            if len(name.split(" ")) < 2:
                if input("Only one name found. Is this a device? (y/n) ").lower() == "y":
                    names[" ".join([i.strip() for i in name.split()])] = "no-encrypt"

                else:
                    names[" ".join([i.strip() for i in name.split()])] = "encrypt"

        print("Creating QR codes for the following names:")
        for name, proc in names.items():
            print(f"  --> {name:<20} ({proc})")

        if input("Continue? (y/n) ").lower() == 'y':
            validation_json: dict[str, str] = read("resources/data/validation.json", exit_on_error=True)
            for entry, processing in names.items():
                stripped: str = entry.strip()

                if processing == "encrypt":
                    try:
                        data: str = sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                        if data in validation_json:
                            raise ValueError

                        qr.make(data).save(f"{path_out}/{stripped}.png")
                        add_text_f(f"{path_out}/{stripped}.png", stripped)

                    except FileNotFoundError:
                        tc.print_fail("File not found. Check logs for more info")
                        write_log()
                        exit(1)

                    except ValueError:
                        tc.print_fail("Found duplicate entry in validation. Check logs for more info")
                        write_log()
                        exit(1)

                    validation_json[data] = stripped
                    write("resources/data/validation.json", validation_json)

                else:
                    qr.make(stripped).save(f"{path_out}/{stripped}.png")
                    add_text_f(f"{path_out}/{stripped}.png", stripped)
