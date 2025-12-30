import os
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

CURR_ABS_PATH = os.path.abspath("")


class FileSystemItem:
    def __init__(self, abs_path: str):
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

    def full_name(self):
        name = self.name if self.name else ""
        ext = f".{self.extension}" if self.extension else ""
        return name + ext

    def is_image(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        if self.extension == "jpg" or self.extension == "png":
            return True

        return False


class Result:
    def __init__(self, result, is_successful: bool = True, err_msg: str | None = None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"


def list_of_fs_items_at(abs_path: str, images_only: bool = False):
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
        fs_item = FileSystemItem(abs_path)
        if images_only:
            if fs_item.is_image():
                files.append(fs_item)
        else:
            files.append(fs_item)

    return Result(files)


def prompt_path():
    print("Display all items at a given path")
    print("Enter path:")
    path = input().strip()

    return path if path else ""


def gui():
    path = os.path.abspath("gitignore")
    list = list_of_fs_items_at(path, images_only=True)
    if not list.is_successful:
        print(list.formatted_err_msg())
        return

    fs_items_size = len(list.result)
    fs_item_counter = -1

    # main window
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.title("Vim Photo Manager")

    # components
    currect_abs_path_l = tk.Label(root, text=path)
    file_l = tk.Label(root, text=f"Number of images = {fs_items_size}")
    mapped_key_press_l = tk.Label(root, text="Mapped key")
    command_l = tk.Label(root, text="Command")
    image_l = tk.Label(root, text="Picture place")

    # packing
    currect_abs_path_l.pack()
    file_l.pack()
    command_l.pack()
    mapped_key_press_l.pack()
    image_l.pack(expand=True, fill=tk.BOTH)

    if fs_items_size == 0:
        file_l.config(text="No images here")

    def event_char(char):
        return f"'{char}'"

    def on_escape(event):
        root.quit()

    def on_left(event):
        mapped_key_press_l.config(text=event_char(event.char))

        nonlocal fs_item_counter

        if fs_items_size == 0:
            command_l.config(text="No image")
            return

        fs_item_counter = np.clip(fs_item_counter - 1, 0, fs_items_size - 1)
        file_l.config(text=list.result[fs_item_counter].full_name())
        command_l.config(text="Prev photo")
        display_image_from_path(list.result[fs_item_counter].abs_path)

    def on_right(event):
        mapped_key_press_l.config(text=event_char(event.char))
        nonlocal fs_item_counter

        if fs_items_size == 0:
            command_l.config(text="No image")
            return

        fs_item_counter = np.clip(fs_item_counter + 1, 0, fs_items_size - 1)
        file_l.config(text=list.result[fs_item_counter].full_name())
        command_l.config(text="Next photo")
        display_image_from_path(list.result[fs_item_counter].abs_path)

    def any_key(event):
        mapped_key_press_l.config(text=event_char(event.char))
        command_l.config(text=event.keysym)

    def display_image_from_path(path: str):
        img = Image.open(path)
        img.thumbnail(
            (root.winfo_screenwidth(), root.winfo_screenheight()),
            Image.Resampling.LANCZOS,
        )
        photo = ImageTk.PhotoImage(img)
        image_l.config(image=photo)
        image_l.image = photo

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
            print("Opening GUI")
            gui()
        elif choice == i_cli:
            print("Opening CLI")
            cli()
        else:
            print("Invalid choice")
            continue
        break

    print("\n\n----- End of the program -----")
