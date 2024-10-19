import json
import base64
import requests
from hashlib import sha256
from pwinput import pwinput
from requests import Response
from resources.scripts.TermColor import TermColor
from resources.scripts.Exceptions import StopExecution

tc = TermColor()


def _pull(pwd: str) -> None:
    """Retrieves data from AWS and stores it in local files.

    Args:
        pwd: The password to authenticate with the AWS endpoint.
    """

    url: str = "https://tryobgwrhsrnbyq5re77znzxry0brhfc.lambda-url.ca-central-1.on.aws/"
    returned: str = requests.post(url, data={"pass": sha256(pwd.encode()).hexdigest()}).content.decode("utf-8")

    if returned == "Unauthorized: Bad password":
        tc.print_fail(returned)
        raise StopExecution

    returned_data: dict = json.loads(returned)

    # Store API key data
    with open("resources/data/api_key.json", "w") as api:
        json.dump(json.loads(returned_data["api_key"]), api, indent=4)

    # Store validation data
    with open("resources/data/validation.json", "w") as val:
        json.dump(json.loads(returned_data["validation"]), val, indent=4)


def _push(data: dict, kind: str, pwd: str) -> str:
    """Sends data to AWS for storage.

    Args:
        data: The data to send to AWS.
        kind: The type of data being sent.
        pwd: The password to authenticate with the AWS endpoint.

    Returns:
        The response content from the AWS endpoint.
    """

    params: dict = {
        "pass": sha256(pwd.encode()).hexdigest(),
        "kind": kind,
        "data": base64.urlsafe_b64encode(json.dumps(data).encode())
    }

    resp: Response = requests.post("https://i5nqbfht5a6v4epzr5anistot40qkyaz.lambda-url.ca-central-1.on.aws/",
                                   data=params
                                   )
    return resp.content.decode("utf-8")


def handle_sync() -> None:
    """Prompts the user to synchronize with AWS."""

    if input("Sync local machine with AWS? (y/n) ").lower() == "y":
        aws_key: str = pwinput()
        _pull(aws_key)
        print("Finished syncing local machine")

    if input("Sync AWS with local machine? (y/n) ").lower() == "y":
        aws_key: str = pwinput()
        with open("resources/data/api_key.json", "r") as api:
            _push(json.load(api), "apikey", aws_key)

        with open("resources/data/validation.json", "r") as val:
            _push(json.load(val), "validation", aws_key)

        print("Finished syncing AWS")
