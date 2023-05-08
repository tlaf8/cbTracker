import subprocess as sp
from platform import system
from sys import exit
from time import sleep

ans = input("This program will install all necessary packages and build the project. Continue? (y/N) ")
if ans == "y":
    print("Get ready to see a lot of text!")
    print("Creating virtual environment...")
    sp.call("python -m venv venv".split(" "))

    device = system()
    if device == "Linux":
        print("Running on Linux! Time to install and build.")
        sp.call("venv/bin/python -m pip install --upgrade pip".split())
        sp.call("venv/bin/pip install -r resources/requirements.txt".split())
        sp.call("venv/bin/pyinstaller main.py".split())

    elif device == "Windows":
        print("Running on Windows! Time to install and build.")
        sp.call(r".\venv\Scripts\python.exe -m pip install --upgrade pip".split())
        sp.call(r".\venv\Scripts\pip.exe install -r .\resources\requirements.txt".split())
        sp.call(r".\venv\Scripts\pyinstaller.exe main.py".split())

    elif device == "Darwin":
        print("Running on MacOS. Attempting with Linux commands...")
        try:
            print("Time to install and build.")
            sp.call("venv/bin/python -m pip install --upgrade pip".split())
            sp.call("venv/bin/pip install -r resources/requirements.txt".split())
            sp.call("venv/bin/pyinstaller main.py".split())

        except Exception as e:
            print("Well that didn't work. Send an email to 21laforgth@gmail.com so he can add support for MacOS.")
            print(e)
            exit(1)

    print("Finished! You can close this window now. Make sure to take a look at README.md!")
    print("Automatically closing in 10 seconds...")
    sleep(10)
    exit(0)

else:
    print("Aborting.")
    exit(0)
