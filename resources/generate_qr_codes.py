import qrcode
import hashlib
from filelib import read_file, write_file

lines = read_file(r"classlist.txt")
secret = input("Please enter a secret to encrypt with: ")
open("resources/validation.txt", "w").close()

codes = []
for entry in lines:
    temp = hashlib.sha256((entry + secret).encode()).hexdigest()
    qrcode.make(temp).save(rf"qr_codes/{entry}.png")
    codes.append(temp)

write_file(r"resources/validation.txt", codes)
