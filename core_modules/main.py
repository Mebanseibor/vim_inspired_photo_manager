import os
import numpy as np
import customtkinter as ctk
import xxhash
import pickle
from PIL import Image

CURR_ABS_PATH = os.path.abspath("")


IMAGE_FG_COLOR_DEFAULT = 0
IMAGE_FG_COLOR_KEEP = 1
IMAGE_FG_COLOR_DELETE = 2
IMAGE_FG_COLOR_TO_REVIEW = 3

COLORS = {
    IMAGE_FG_COLOR_DEFAULT: "white",
    IMAGE_FG_COLOR_KEEP: "green",
    IMAGE_FG_COLOR_DELETE: "red",
    IMAGE_FG_COLOR_TO_REVIEW: "yellow",
}

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]

CACHE_FOLDER = "cache"


class FileSystemItem:
    def __init__(self, abspath: str):
        self.abspath: str = abspath
        self.is_file: bool | None = os.path.isfile(abspath)

        if self.is_file:
            split_name = os.path.basename(abspath).rsplit(".")
            self.name = (
                None
                if split_name[0] == ""
                else split_name[0]
                if len(split_name) == 1
                else ".".join(split_name[0:-1])
            )
            self.extension = None if len(split_name) == 1 else split_name[-1]
        else:
            self.name = os.path.basename(abspath)
            self.extension = None

        self.extension = self.extension.lower() if self.extension else self.extension

        self.file_hash: str | None = (
            hashFile(abspath, self.full_name()) if self.is_file else None
        )

    def display_details(self):
        print(f"full_name():\t{self.full_name()}")
        print(f"is_file:\t{self.is_file}")
        print(f"is_image():\t{self.is_image()}")
        print(f"name:\t\t{self.name}")
        print(f"extension:\t{self.extension}")
        print(f"file_hash:\t{self.file_hash}")
        print(f"abs_path:\t{self.abspath}")

    def full_name(self):
        name = self.name if self.name else ""
        ext = f".{self.extension}" if self.extension else ""
        return name + ext

    def is_image(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        return self.extension in IMAGE_EXTENSIONS


class FSItemGUIHandler:
    def __init__(self, fs_item: FileSystemItem, image):
        self.image = image
        self.highlight_color: int = IMAGE_FG_COLOR_DEFAULT
        self.fs_item: FileSystemItem = fs_item

    def update_highlight(self, image_label, fg_color: int):
        fg_color_str = COLORS.get(fg_color, IMAGE_FG_COLOR_DEFAULT)
        image_label.configure(fg_color=fg_color_str)
        self.highlight_color = fg_color


class Result:
    def __init__(self, result, is_successful: bool = True, err_msg: str | None = None):
        self.is_successful = is_successful
        self.err_msg = err_msg
        self.result = result

    def formatted_err_msg(self):
        return f"Error: {self.err_msg}"


def list_of_fs_items_at(
    abs_path: str, images_only: bool = False, max_items: int | None = None
):
    dir_path = os.path.join(CURR_ABS_PATH, abs_path)

    if not os.path.exists(dir_path):
        return Result(None, False, f"Path '{abs_path}' does not exist")

    if not os.path.isdir(dir_path):
        return Result(None, False, f"Path '{abs_path}' was not a directory")

    # creating a fs_item
    file_paths = os.listdir(dir_path)
    files = []
    counter_file_paths = 0
    counter_selected_items = 0
    for file_path in file_paths:
        joined_path = os.path.join(dir_path, file_path)
        abs_path = os.path.abspath(joined_path)
        fs_item = FileSystemItem(abs_path)
        counter_file_paths += 1
        progress = counter_file_paths / len(file_paths) * 100
        print(f"Checked file system item ({progress:06.2f}%): {fs_item.full_name()}")
        if images_only:
            if fs_item.is_image():
                files.append(fs_item)
            else:
                continue
        else:
            files.append(fs_item)

        counter_selected_items += 1
        if max_items:
            if counter_selected_items >= max_items:
                break

    print(f"Number of fs items available:\t{len(file_paths)}")
    print(f"Number of fs items selected:\t{counter_selected_items}")

    return Result(files)


def prompt_path():
    print("Display all items at a given path")
    print("Enter path:")
    path = input().strip()

    return path if path else ""


def hashFile(abspath_file: str, salt: str):
    hasher = xxhash.xxh64()

    hasher.update(salt.encode())

    fd = os.open(abspath_file, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    try:
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            hasher.update(chunk)
    finally:
        os.close(fd)
    return hasher.hexdigest()


def cacheImage(img_obj: FSItemGUIHandler, expect_no_clash: bool = False) -> bool:
    if not img_obj.fs_item.file_hash:
        return False

    abspath_cache_folder = os.path.abspath(CACHE_FOLDER)

    abspath_cache_obj = os.path.abspath(
        os.path.join(abspath_cache_folder, img_obj.fs_item.file_hash)
    )

    if expect_no_clash and os.path.exists(abspath_cache_obj):
        return False

    with open(abspath_cache_obj, "wb") as file:
        pickle.dump(img_obj, file)

    return True


def isImageCached(image_hash: str) -> bool:
    abspath_cache_folder = os.path.join(CACHE_FOLDER)

    for path_file in os.listdir(abspath_cache_folder):
        if path_file == image_hash:
            return True
    return False


def getCachedImage(image_hash: str):
    abspath_cache = os.path.abspath(CACHE_FOLDER)
    abspath_cached_image = os.path.join(abspath_cache, image_hash)
    with open(abspath_cached_image, "rb") as file:
        imgObj = pickle.load(file)
        return imgObj


def gui():
    path = os.path.abspath("gitignore/test")
    print(f"Getting files at {path}")
    list_fs_items = list_of_fs_items_at(path, images_only=True)
    if not list_fs_items.is_successful:
        print(list_fs_items.formatted_err_msg())
        return
    print("Completed getting files")

    fs_items_size = len(list_fs_items.result)
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

    image_gui_handlers: list[FSItemGUIHandler] = []

    def update_system_log_l(log: str):
        nonlocal system_log_l
        system_log_l.configure(text=log)
        print(log)

    def event_char(char):
        return f"'{char}'"

    def on_escape(event):
        root.quit()

    def on_previous(event):
        update_system_log_l("Displaying previous image")
        mapped_key_press_l.configure(text=event_char(event.char))

        nonlocal fs_item_curr_index

        if fs_items_size == 0:
            command_l.configure(text="No image")
            return

        fs_item_curr_index = np.clip(fs_item_curr_index - 1, 0, fs_items_size - 1)
        file_l.configure(text=list_fs_items.result[fs_item_curr_index].full_name())
        command_l.configure(text="Prev photo")
        display_image_from_path(fs_item_curr_index)

    def on_next(event):
        update_system_log_l("Displaying next image")
        mapped_key_press_l.configure(text=event_char(event.char))
        nonlocal fs_item_curr_index

        if fs_items_size == 0:
            command_l.configure(text="No image")
            return

        fs_item_curr_index = np.clip(fs_item_curr_index + 1, 0, fs_items_size - 1)
        file_l.configure(text=list_fs_items.result[fs_item_curr_index].full_name())
        command_l.configure(text="Next photo")
        display_image_from_path(fs_item_curr_index)

    def on_deletion(event):
        update_system_log_l("Deleting")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to delete")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_DELETE)
        cacheImage(h)

    def on_keep(event):
        update_system_log_l("Keep")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to keep")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_KEEP)
        cacheImage(h)

    def on_clear(event):
        update_system_log_l("Clear")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to clear")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_DEFAULT)
        cacheImage(h)

    def on_review(event):
        update_system_log_l("Review")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to review")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_TO_REVIEW)
        cacheImage(h)

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
        h.update_highlight(image_l, h.highlight_color)

    def init():
        update_system_log_l("Pre-creating FSItemGUIHandler objects")
        count_processed_images = 0

        for image in list_fs_items.result:
            count_processed_images += 1
            progress = count_processed_images / len(list_fs_items.result) * 100
            update_system_log_l(
                f"Processing ({count_processed_images}/{len(list_fs_items.result)}, {progress:06.2f}%):\t{image.full_name()}"
            )

            image_hash = hashFile(image.abspath, image.full_name())
            if isImageCached(image_hash):
                update_system_log_l(f"Getting cached image:\t\t{image.file_hash}")
                imgObj = getCachedImage(image_hash)
            else:
                update_system_log_l(f"Creating: cache item:\t\t{image.full_name()}")

                img = Image.open(image.abspath)
                img.thumbnail(
                    (root.winfo_screenwidth(), root.winfo_screenheight()),
                    Image.Resampling.BICUBIC,
                )
                imgObj = FSItemGUIHandler(image, img)
                if not cacheImage(imgObj, expect_no_clash=True):
                    update_system_log_l(f"Cannot cache image: {image.full_name()}")
                    continue

            image_gui_handlers.append(imgObj)

        nonlocal fs_item_curr_index
        fs_item_curr_index = np.clip(fs_item_curr_index - 1, 0, fs_items_size - 1)
        file_l.configure(text=list_fs_items.result[fs_item_curr_index].full_name())
        display_image_from_path(fs_item_curr_index)

    # escape keys
    root.bind("<Escape>", on_escape)
    root.bind("q", on_escape)

    # picture operations
    root.bind("j", on_deletion)
    root.bind("k", on_keep)
    root.bind("c", on_clear)
    root.bind("m", on_review)

    # navigation
    root.bind("l", on_next)
    root.bind("h", on_previous)

    # any keys
    root.bind("<Key>", any_key)

    root.after(50, init)
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

    def makeFolders():
        abspath_cache_folder = os.path.abspath(CACHE_FOLDER)

        if not os.path.exists(abspath_cache_folder):
            print("Creating non-existant cache folder")
            os.makedirs(abspath_cache_folder)

    makeFolders()

    command_quit = "q!"

    # choosing an interface
    i_gui = "1"
    i_cli = "2"
    while True:
        print("\n\n")
        print(f"To quit, enter: '{command_quit}'")
        print("Pick an interface:")
        print(f"{i_gui}. GUI (With window interface)")
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
