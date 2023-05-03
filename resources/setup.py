import subprocess
import platform

print("This tool will automatically run pip and install necessary packages in a virtual environment.")
if input("Continue? (y/n) ").lower() == "n":
    exit(-1)

system = platform.system()
if system == "Linux":
    subprocess.call(["python", "-m", "venv", "venv"])
    print("Virtual environment created. Installing packages.")
    subprocess.call(["venv/bin/pip3", "install", "-r", "resources/requirements.txt"])

elif system == "Windows":
    print("Windows is not supported just yet. Still in development on a Linux machine.")

elif system == "Darwin":
    print("MacOS is not supported just yet. Still in development on a Linux machine.")

else:
    print("What computer is this running on?!?!?")

print("Finished!")
