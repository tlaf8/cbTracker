class BadOrderException(Exception):
    def __init__(self):
        super().__init__("Not scanned in correct order")


class UnknownQRCodeException(Exception):
    def __init__(self):
        super().__init__("QR code is not recognized")


class StopExecution(Exception):
    def __init__(self):
        super().__init__("Program quit. Stop timer execution")
