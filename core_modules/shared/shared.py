CURR_ABS_PATH: str | None = None
BASE_ABS_PATH: str | None = None
BASE_FILEPATHS: dict[str, list[str]] | None = None

APP_WIDTH: int | None = None
APP_HEIGHT: int | None = None


class Result:
    def __init__(self, result, is_successful: bool = True, err_msg: str | None = None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"
