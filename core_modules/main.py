import os

CURR_ABS_PATH = os.path.abspath("")


class FileSystemItem:
    def __init__(self, abs_path):
        self.abs_path = abs_path
        self.is_file = os.path.isfile(abs_path)

        if self.is_file:
            split_name = os.path.basename(abs_path).rsplit(".")
            self.name = (
                None
                if split_name[0] == ""
                else split_name[0]
                if len(split_name) == 1
                else ".".join(split_name[0:-1])
            )
            self.extension = None if len(split_name) == 1 else split_name[-1]
        else:
            self.name = os.path.basename(abs_path)
            self.extension = None

    def display_details(self):
        print(f"abs_path:\t{self.abs_path}")
        print(f"is_file:\t{self.is_file}")
        print(f"name:\t\t{self.name}")
        print(f"extension:\t{self.extension}")


class Result:
    def __init__(self, result, is_successful=True, err_msg=None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"


def list_of_fs_items_at(abs_path):
    dir_path = os.path.join(CURR_ABS_PATH, abs_path)

    if not os.path.exists(dir_path):
        return Result(None, False, f"Path '{abs_path}' does not exist")

    if not os.path.isdir(dir_path):
        return Result(None, False, f"Path '{abs_path}' was not a directory")

    # creating a fs_item
    file_paths = os.listdir(dir_path)
    files = []
    for file_path in file_paths:
        joined_path = os.path.join(dir_path, file_path)
        abs_path = os.path.abspath(joined_path)
        files.append(FileSystemItem(abs_path))

    return Result(files)


def prompt_path():
    print("Display all items at a given path")
    print("Enter path:")
    path = input().strip()

    return path if path else ""


if __name__ == "__main__":
    print("\n\n----- Start of the program -----\n\n")

    command_quit = "!q"
    while True:
        print("\n\n")
        print(f"Current absolute path:\t{CURR_ABS_PATH}")
        print(f"To quit, enter: '{command_quit}'")
        path = prompt_path()
        if path == command_quit:
            break

        abs_path = os.path.join(CURR_ABS_PATH, path)

        if not os.path.exists(abs_path):
            print(f"Path does not exist: {abs_path}")
            continue

        if not os.path.isdir(abs_path):
            print(f"Path is not a directory: {abs_path}")
            continue

        list = list_of_fs_items_at(abs_path)

        if not list.is_successful:
            print(list.formatted_err_msg())
            exit()

        for item in list.result:
            item.display_details()
            print("\n")

    print("\n\n----- End of the program -----")
