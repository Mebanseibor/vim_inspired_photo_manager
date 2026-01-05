import os

CURR_ABS_PATH = os.path.abspath("")


class Result:
    def __init__(self, result, is_successful: bool = True, err_msg: str | None = None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"
