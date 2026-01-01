import os
import numpy as np
import customtkinter as ctk
from PIL import Image

CURR_ABS_PATH = os.path.abspath("")

DEFAULT_COLOR_NEUTRAL = "gray"
DEFAULT_COLOR_DELETED = "red"

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]


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

        self.extension = self.extension.lower() if self.extension else self.extension

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

        if self.extension in IMAGE_EXTENSIONS:
            return True

        return False


class FSItemGUIHandler:
    def __init__(self, image):
        self.image = image
        self.is_highlighted: bool = False

    def toggleHighlight(self):
        self.is_highlighted = not self.is_highlighted

    def update_highlight(self, image_label):
        if self.is_highlighted:
            image_label.configure(fg_color=DEFAULT_COLOR_DELETED)
        else:
            image_label.configure(fg_color=DEFAULT_COLOR_NEUTRAL)


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
    path = os.path.abspath("gitignore/test")
    list = list_of_fs_items_at(path, images_only=True)
    if not list.is_successful:
        print(list.formatted_err_msg())
        return

    fs_items_size = len(list.result)
    fs_item_curr_index = -1

    # main window
    root = ctk.CTk()
    root.attributes("-fullscreen", True)
    root.title("Vim Photo Manager")

    # components
    currect_abs_path_l = ctk.CTkLabel(root, text=path)
    file_l = ctk.CTkLabel(root, text=f"Number of images = {fs_items_size}")
    mapped_key_press_l = ctk.CTkLabel(root, text="Mapped key")
    command_l = ctk.CTkLabel(root, text="Command")
    system_log_l = ctk.CTkLabel(root, text="System Logs")
    image_l = ctk.CTkLabel(root, text="")

    # packing
    currect_abs_path_l.pack()
    file_l.pack()
    command_l.pack()
    mapped_key_press_l.pack()
    system_log_l.pack()
    image_l.pack(expand=True, fill=ctk.BOTH)

    if fs_items_size == 0:
        file_l.configure(text="No images here")

    image_gui_handlers = []

    def update_system_log_l(log: str):
        nonlocal system_log_l
        system_log_l.configure(text=log)
        print(log)

    def event_char(char):
        return f"'{char}'"

    def on_escape(event):
        root.quit()

    def on_left(event):
        update_system_log_l("displaying left image")
        mapped_key_press_l.configure(text=event_char(event.char))

        nonlocal fs_item_curr_index

        if fs_items_size == 0:
            command_l.configure(text="No image")
            return

        fs_item_curr_index = np.clip(fs_item_curr_index - 1, 0, fs_items_size - 1)
        file_l.configure(text=list.result[fs_item_curr_index].full_name())
        command_l.configure(text="Prev photo")
        display_image_from_path(fs_item_curr_index)

    def on_right(event):
        update_system_log_l("displaying right image")
        mapped_key_press_l.configure(text=event_char(event.char))
        nonlocal fs_item_curr_index

        if fs_items_size == 0:
            command_l.configure(text="No image")
            return

        fs_item_curr_index = np.clip(fs_item_curr_index + 1, 0, fs_items_size - 1)
        file_l.configure(text=list.result[fs_item_curr_index].full_name())
        command_l.configure(text="Next photo")
        display_image_from_path(fs_item_curr_index)

    def on_deletion(event):
        update_system_log_l("deleting")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Deleting photo")
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.toggleHighlight()
        h.update_highlight(image_l)

    def any_key(event):
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text=event.keysym)

    def display_image_from_path(index: int):
        def get_fitted_size(img, max_w, max_h):
            orig_w, orig_h = img.size
            ratio = min(max_w / orig_w, max_h / orig_h)
            return int(orig_w * ratio), int(orig_h * ratio)

        nonlocal image_gui_handlers
        h = image_gui_handlers[index]
        img = h.image
        photo = ctk.CTkImage(
            img,
            size=get_fitted_size(img, image_l.winfo_width(), image_l.winfo_height()),
        )
        image_l.configure(image=photo)
        h.update_highlight(image_l)

    def init():
        update_system_log_l("Pre-creating FSItemGUIHandler objects")
        count_cache = 1

        for image in list.result:
            update_system_log_l(
                f"Caching ({count_cache}/{len(list.result)}): {image.abs_path}"
            )
            img = Image.open(image.abs_path)
            img.thumbnail(
                (root.winfo_screenwidth(), root.winfo_screenheight()),
                Image.Resampling.BICUBIC,
            )
            image_gui_handlers.append(FSItemGUIHandler(img))
            count_cache += 1

    # escape keys
    root.bind("<Escape>", on_escape)
    root.bind("q", on_escape)

    # navigation
    root.bind("h", on_left)
    root.bind("l", on_right)

    # deletion
    root.bind("x", on_deletion)

    # any keys
    root.bind("<Key>", any_key)

    root.after(10, init)
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

    command_quit = "q!"

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
