import os

BASE_PATH = "./"


class FileSystemItem:
    def __init__(self, abs_path, is_file, extension=None):
        self.abs_path = abs_path
        self.is_file = is_file
        self.extension = extension

        if is_file and not extension:
            with open(abs_path, "r") as file:
                self.extension = file.name.rsplit(".")[1]

    def display_details(self):
        print(f"abs_path:\t{self.abs_path}")
        print(f"is_file:\t{self.is_file}")
        print(f"extension:\t{self.extension}")


class Result:
    def __init__(self, result, is_successful=True, err_msg=None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"


def list_of_fs_items_at(path):
    dir_path = os.path.join(BASE_PATH, path)

    if not os.path.exists(dir_path):
        return Result(None, False, f"Path '{path}' does not exist")

    if not os.path.isdir(dir_path):
        return Result(None, False, f"Path '{path}' was not a directory")

    # creating a fs_item
    file_paths = os.listdir(dir_path)
    files = []
    for file_path in file_paths:
        joined_path = os.path.join(dir_path, file_path)
        abs_path = os.path.abspath(joined_path)
        files.append(FileSystemItem(abs_path, os.path.isfile(abs_path)))

    return Result(files)


def prompt_path():
    print("Display all items at a given path")
    print("Enter path:")
    path = input().strip()

    return path if path else ""


if __name__ == "__main__":
    print("\n\n----- Start of the program -----\n\n")

    path = prompt_path()

    list = list_of_fs_items_at(path)

    if not list.is_successful:
        print(list.formatted_err_msg())
        exit()

    for item in list.result:
        item.display_details()
        print("\n")

    print("\n\n----- End of the program -----")
