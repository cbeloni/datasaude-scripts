import logging

class Log(logging.Logger):

    def __init__(self, nome):
        super().__init__(nome)
        self.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s -  %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)
