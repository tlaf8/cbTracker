import cv2
import numpy as np
import qrcode as qr
from gspread import Cell
from hashlib import sha256
from pwinput import pwinput
from PIL import ImageFont, Image, ImageDraw
from resources.scripts.AWS import handle_sync
from resources.scripts.Logging import write_log
from resources.scripts.FileIO import read, write
from resources.scripts.TermColor import TermColor
from resources.scripts.ImageTools import add_text
from resources.scripts.Exceptions import BadOrderException, UnknownQRCodeException, StopExecution

tc = TermColor()


class QRProcessor:
    def __init__(self, hash_dict: dict[str, str]):
        """Initializes the QR processor with dictionaries for lookups and camera resources.

        Args:
            hash_dict: A dictionary containing hashed QR code data for students.
        """
        self.hash_dict: dict[str, str] = hash_dict
        self.decoder: cv2.QRCodeDetector = cv2.QRCodeDetector()
        self.loading: np.ndarray = cv2.imread("resources/img/loading.png")
        self.scan_img: np.ndarray = cv2.imread("resources/img/scan_img.png")

    def read_code(self, message: str, device_names: list[str]) -> str:
        """Reads a QR code from the camera.

        Args:
            message: A message to display on the camera preview.
            device_names: A list of strings that contain valid devices.

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
                raise StopExecution

            raw_result: str
            raw_result, _, _ = self.decoder.detectAndDecode(raw_frame)
            if raw_result != "":
                if raw_result not in device_names and raw_result not in self.hash_dict.keys():
                    badin: np.ndarray = add_text(self.loading.copy(), "Unrecognized QR Code", [10, 30])
                    cv2.imshow("Scanner", badin)
                    cv2.waitKey(3000)
                    raise UnknownQRCodeException

                tc.print_ok(f"Read value: {raw_result}")
                cam.release()
                return raw_result

            settings: dict[str, str | int] = read("resources/data/settings.json")
            frame: np.ndarray = cv2.flip(raw_frame, 1)
            frame = cv2.rectangle(frame, (0, 0), (225, 75), (255, 255, 255), -1)
            frame = add_text(frame, message, [10, 30])
            frame = add_text(frame, "Press 'q' to quit", [10, 60])
            frame = cv2.resize(frame, (settings["window x"], settings["window y"]), interpolation=cv2.INTER_AREA)
            cv2.namedWindow("Scanner", flags=cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow("Scanner", settings["window x"], settings["window y"])
            cv2.imshow("Scanner", frame)

            # Handle key presses
            key: int = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                cam.release()
                tc.print_ok("Exiting")
                raise StopExecution

            elif key == ord('s'):
                cv2.destroyAllWindows()
                handle_sync()

            elif key == ord('n'):
                cv2.destroyAllWindows()
                self.create_qr_codes(
                    "resources/qr_codes/output",
                    fuzz=pwinput(f"Fuzzer for convolution (Ex. John{tc.format('fuzz', 'fail')}Doe): ")
                )

    def process_code(self, data: str, accepted_devices: list[str], expecting: str) -> str:
        """Processes the decoded QR code data based on expectations.

        Args:
            data: The decoded QR code data.
            accepted_devices: A list containing accepted device names.
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

        elif data in accepted_devices:
            obtained: np.ndarray = add_text(self.scan_img.copy(), f"Obtained: {data}", [10, 30])
            cv2.imshow("Scanner", obtained)
            cv2.waitKey(500)

            if expecting == "rental":
                return data

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

        while (name := input("Enter full name of student/rental: ")) != "":
            if len(name.split(" ")) < 2:
                if input("Only one name found. Is this a device? (y/n) ").lower() == "y":
                    names[" ".join([i.strip() for i in name.split()])] = "no-encrypt"

            else:
                names[" ".join([i.strip() for i in name.split()])] = "encrypt"

        print("Creating QR codes for the following names:")
        for name, proc in names.items():
            print(f"  --> {name:<20} ({proc})")

        if input("Continue? (y/n) ").lower() == 'y':
            font: ImageFont = ImageFont.truetype("resources/data/RobotoMono-Regular.ttf", size=16)
            validation_json: dict[str, str] = read("resources/data/validation.json", exit_on_error=True)
            for entry, processing in names.items():
                stripped: str = entry.strip()

                if processing == "encrypt":
                    try:
                        data: str = sha256(fuzz.join(stripped.split()).encode()).hexdigest()
                        if data in validation_json:
                            raise ValueError

                        result: Image = qr.make(data).get_image()

                    except FileNotFoundError:
                        tc.print_fail("File not found. Check logs for more info")
                        write_log()
                        raise StopExecution

                    except ValueError:
                        tc.print_fail("Found duplicate entry in validation. Check logs for more info")
                        write_log()
                        raise StopExecution

                    validation_json[data] = stripped
                    write("resources/data/validation.json", validation_json)

                else:
                    result: Image = qr.make(stripped).get_image()

                width, height = result.size
                artist: ImageDraw = ImageDraw.Draw(result)
                artist.text(
                    (width / 2 - font.getlength(stripped) / 2, height - 30),
                    stripped,
                    font=font
                )
                result.save(f"{path_out}/{stripped}.png")
