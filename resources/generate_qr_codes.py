import qrcode
import hashlib
from filelib import read_file, write_file

lines = read_file(r"classlist.txt")
secret = input("Please enter a secret to encrypt with: ")
open("resources/validation.json", "w").close()

codes = {}
for entry in lines:
    temp = hashlib.sha256((entry + secret).encode()).hexdigest()
    qrcode.make(temp).save(rf"qr_codes/{entry}.png")
    codes[entry] = temp

write_file(r"resources/validation.json", {v: k for k, v in codes.items()})
