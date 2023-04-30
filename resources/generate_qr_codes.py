import qrcode

with open("classlist.txt", "r") as students:
    lines = [line.rstrip() for line in students if line != "\n"]

for entry in lines:
    qrcode.make(entry).save(f"qr_codes\\{entry}.png")

