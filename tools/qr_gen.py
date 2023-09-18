import qrcode
import json
from os import walk, mkdir
from os.path import exists

# Make sure 'qrcodes' exists
if not exists("../resources/qr_codes"):
    mkdir("../resources/qr_codes")

# Create qr code for each entry in each file
for filename in next(walk("../resources/validations"))[2]:
    if not exists(f"../resources/qr_codes/{filename[:-4:]}"):
        mkdir(f"../resources/qr_codes/{filename[:-4:]}")

    with open(f"../resources/validations/{filename}", "r") as temp:
        data = json.load(temp)
        for name, val in data.items():
            print(f"Running {name} from {filename}")
            qr_obj = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_Q,
                border=10
            )
            qr_obj.add_data(val)
            qr_obj.make_image().save(f"../resources/qr_codes/{filename[:-4:]}/{name}.png")

