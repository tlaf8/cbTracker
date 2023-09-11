import json
from os import walk

big_boy = dict()
for filename in next(walk("outputs"))[2]:
    with open(f"outputs/{filename}", "r") as temp:
        big_boy.update(json.load(temp))

with open("outputs/validation.json", "w") as out:
    json.dump(big_boy, out, indent=4)
