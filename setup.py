import subprocess as sp
from platform import system
from sys import exit

print("This file is deprecated!")
print("If you would like to compile, remove the 3 quotation marks and run the file itself.")
print("No guarantees that this will run. It is better to make a shortcut to run python command.")

"""

ans = input("This program will install all necessary packages and build the project. Continue? (y/N) ")
if ans.lower() == "y":
    print("Creating virtual environment...")
    sp.call("python -m venv venv".split(" "))

    device = system()
    if device == "Linux":
        print("Running on Linux! Time to install and build.")
        sp.call("venv/bin/python -m pip install --upgrade pip".split())
        sp.call("venv/bin/pip install -r resources/requirements.txt".split())
        sp.call("venv/bin/pyinstaller main.py -y".split())

    elif device == "Windows":
        print("Running on Windows! Time to install and build.")
        sp.call(r".\venv\Scripts\python.exe -m pip install --upgrade pip".split())
        sp.call(r".\venv\Scripts\pip.exe install -r .\resources\requirements.txt".split())
        sp.call(r".\venv\Scripts\pyinstaller.exe main.py -y".split())

    elif device == "Darwin":
        print("Running on MacOS. Attempting with Linux commands...")
        try:
            print("Time to install and build.")
            sp.call("venv/bin/python -m pip install --upgrade pip".split())
            sp.call("venv/bin/pip install -r resources/requirements.txt".split())
            sp.call("venv/bin/pyinstaller main.py -y".split())

        except Exception as e:
            print("Well that didn't work. Send an email to 21laforgth@gmail.com so he can add support for MacOS.")
            print(e)
            exit(1)

    print("Finished! You can close this window now. Make sure to take a look at README.md!")
    input("Press ENTER to exit...")
    exit(0)

else:
    print("Aborting.")
    exit(0)
    
"""