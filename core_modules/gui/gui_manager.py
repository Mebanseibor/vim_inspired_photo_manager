import os

import customtkinter as ctk
import numpy as np
from PIL import Image

from ..cache_management import cache_manager as cM
from ..file_system_management import file_system_manager as fsM

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


class FSItemGUIHandler:
    def __init__(self, fs_item: fsM.FileSystemItem, image):
        self.image = image
        self.highlight_color: int = IMAGE_FG_COLOR_DEFAULT
        self.fs_item: fsM.FileSystemItem = fs_item

    def update_highlight(self, image_label, fg_color: int):
        fg_color_str = COLORS.get(fg_color, IMAGE_FG_COLOR_DEFAULT)
        image_label.configure(fg_color=fg_color_str)
        self.highlight_color = fg_color


def gui():
    while True:
        path = fsM.promptPath(prompt_till_valid=True, quit_command="!q")
        if not path:
            return

        abspath_dir = os.path.abspath(path)

        print(f"Getting files at {abspath_dir}")
        list_fs_items = fsM.list_of_fs_items_at(abspath_dir, images_only=True)
        if not list_fs_items.is_successful:
            print(list_fs_items.formatted_err_msg())
            return
        print("Completed getting files")

        if len(list_fs_items.result) != 0:
            break

        print(f"No images was found at this directory: {abspath_dir}\n")

    fs_items_size = len(list_fs_items.result)
    fs_item_curr_index = -1

    # main window
    root = ctk.CTk()
    root.attributes("-fullscreen", True)
    root.title("Vim Photo Manager")

    # components
    currect_abs_path_l = ctk.CTkLabel(root, text=abspath_dir)
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
        cM.cacheImage(h)

    def on_keep(event):
        update_system_log_l("Keep")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to keep")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_KEEP)
        cM.cacheImage(h)

    def on_clear(event):
        update_system_log_l("Clear")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to clear")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_DEFAULT)
        cM.cacheImage(h)

    def on_review(event):
        update_system_log_l("Review")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to review")
        if fs_item_curr_index == -1:
            return
        nonlocal image_gui_handlers
        h = image_gui_handlers[fs_item_curr_index]
        h.update_highlight(image_l, IMAGE_FG_COLOR_TO_REVIEW)
        cM.cacheImage(h)

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

            image_hash = fsM.hashFile(image.abspath, image.full_name())
            if cM.isImageCached(image_hash):
                update_system_log_l(f"Getting cached image:\t\t{image.file_hash}")
                imgObj = cM.getCachedImage(image_hash)
            else:
                update_system_log_l(f"Creating: cache item:\t\t{image.full_name()}")

                img = Image.open(image.abspath)
                img.thumbnail(
                    (root.winfo_screenwidth(), root.winfo_screenheight()),
                    Image.Resampling.BICUBIC,
                )
                imgObj = FSItemGUIHandler(image, img)
                if not cM.cacheImage(imgObj, expect_no_clash=True):
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
