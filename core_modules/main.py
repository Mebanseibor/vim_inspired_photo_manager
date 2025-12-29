import os
import tkinter as tk
from PIL import Image, ImageTk

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


def gui():
    counter = 0

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.title("Vim Photo Manager")
    title_l = tk.Label(root, text="This is the title")
    file_l = tk.Label(root, text=counter)
    mapped_key_press_label = tk.Label(root, text="Press any key")
    command_l = tk.Label(root, text="press_label any key")
    title_l.pack()
    file_l.pack()
    mapped_key_press_label.pack()

    def on_escape(event):
        root.quit()

    def on_left(event):
        nonlocal counter
        counter -= 1
        mapped_key_press_label.config(text=event.char)
        file_l.config(text=counter)
        command_l.config(text="Prev photo")

    def on_right(event):
        nonlocal counter
        counter += 1
        mapped_key_press_label.config(text=event.char)
        file_l.config(text=counter)
        command_l.config(text="Next photo")

    def any_key(event):
        mapped_key_press_label.config(text=event.char)
        command_l.config(text=event.keysym)

    root.bind("<Key>", any_key)
    root.bind("<Escape>", on_escape)
    root.bind("q", on_escape)
    root.bind("h", on_left)
    root.bind("l", on_right)
    root.mainloop()


def cli():
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


if __name__ == "__main__":
    print("\n\n----- Start of the program -----\n\n")

    command_quit = "!q"

    # choosing an interface
    i_gui = "1"
    i_cli = "2"
    while True:
        print("\n\n")
        print(f"To quit, enter: '{command_quit}'")
        print("Pick an interface:")
        print(f"{i_gui}. GUI (With windows)")
        print(f"{i_cli}. CLI (In terminal)")

        choice = input()

        if choice == command_quit:
            break
        elif choice == i_gui:
            gui()
        elif choice == i_cli:
            cli()
        else:
            print("Invalid choice")
            continue
        break

    print("\n\n----- End of the program -----")
