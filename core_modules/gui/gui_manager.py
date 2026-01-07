import os

import customtkinter as ctk
from threading import Event
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


ROOT: ctk.CTk


class FSItemGUIHandler:
    def __init__(self, fs_item: fsM.FileSystemItem, image):
        self.image = image
        self.highlight_color: int = IMAGE_FG_COLOR_DEFAULT
        self.fs_item: fsM.FileSystemItem = fs_item


def gui():
    gui_is_alive_event: Event = Event()
    while True:
        path = fsM.promptPath(prompt_till_valid=True, quit_command="q!")
        if not path:
            return

        abspath_dir = os.path.abspath(path)

        print(f"Getting filepaths at {abspath_dir}")
        filepaths = fsM.getFilePathsAtAbspath(abspath_dir, images_only=True)
        print("Completed getting files")

        if filepaths is None:
            print(f"Can't get filepaths at {abspath_dir}")
            continue

        if len(filepaths) == 0:
            print(f"No images was found at this directory: {abspath_dir}\n")
            continue

        break

    filepaths_size = len(filepaths)

    # main window
    global ROOT
    ROOT = ctk.CTk()
    ROOT.attributes("-fullscreen", True)
    ROOT.title("Vim Photo Manager")

    # components
    currect_abs_path_l = ctk.CTkLabel(ROOT, text=abspath_dir)
    file_l = ctk.CTkLabel(ROOT, text=f"Number of images = {filepaths_size}")
    mapped_key_press_l = ctk.CTkLabel(ROOT, text="Mapped key")
    command_l = ctk.CTkLabel(ROOT, text="Command")
    system_log_l = ctk.CTkLabel(ROOT, text="System Logs")
    image_l = ctk.CTkLabel(ROOT, text="")

    # packing
    currect_abs_path_l.pack()
    file_l.pack()
    command_l.pack()
    mapped_key_press_l.pack()
    system_log_l.pack()
    image_l.pack(expand=True, fill=ctk.BOTH)

    if filepaths_size == 0:
        file_l.configure(text="No images here")

    cacheHandler: cM.ImageItemCacheHandler

    def update_system_log_l(log: str):
        nonlocal system_log_l
        system_log_l.configure(text=log)
        print(log)

    def event_char(char):
        return f"'{char}'"

    def on_escape(event):
        ROOT.quit()

    def on_previous(event):
        update_system_log_l("Displaying previous image")
        mapped_key_press_l.configure(text=event_char(event.char))

        nonlocal cacheHandler

        if filepaths_size == 0:
            command_l.configure(text="No image")
            return

        cacheHandler.prev()
        file_l.configure(text=cacheHandler.getFileNameFromCurr())
        command_l.configure(text="Prev photo")
        loadImageFromCacheHandler()

    def on_next(event):
        update_system_log_l("Displaying next image")
        mapped_key_press_l.configure(text=event_char(event.char))
        nonlocal cacheHandler

        if filepaths_size == 0:
            command_l.configure(text="No image")
            return

        cacheHandler.next()
        file_l.configure(text=cacheHandler.getFileNameFromCurr())
        command_l.configure(text="Next photo")
        loadImageFromCacheHandler()

    def on_deletion(event):
        update_system_log_l("Deleting")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to delete")

        nonlocal cacheHandler
        fg_color = IMAGE_FG_COLOR_DELETE
        if not cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(image_l, fg_color)

    def on_keep(event):
        update_system_log_l("Keep")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to keep")

        nonlocal cacheHandler
        fg_color = IMAGE_FG_COLOR_KEEP
        if not cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(image_l, fg_color)

    def on_clear(event):
        update_system_log_l("Clear")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to clear")

        nonlocal cacheHandler
        fg_color = IMAGE_FG_COLOR_DEFAULT
        if not cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(image_l, fg_color)

    def on_review(event):
        update_system_log_l("Review")
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text="Marking to review")

        nonlocal cacheHandler
        fg_color = IMAGE_FG_COLOR_TO_REVIEW
        if not cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(image_l, fg_color)

    def any_key(event):
        mapped_key_press_l.configure(text=event_char(event.char))
        command_l.configure(text=event.keysym)

    def loadImageFromCacheHandler() -> bool:
        def get_fitted_size(img, max_w, max_h):
            orig_w, orig_h = img.size
            ratio = min(max_w / orig_w, max_h / orig_h)
            return int(orig_w * ratio), int(orig_h * ratio)

        nonlocal cacheHandler
        img = cacheHandler.getImage()
        if not img:
            print("Error: Cannot get Image of cache handler")
            return False
        photo = ctk.CTkImage(
            img,
            size=get_fitted_size(img, image_l.winfo_width(), image_l.winfo_height()),
        )
        image_l.configure(image=photo)
        highlight_color = cacheHandler.getHighlightColor()
        if highlight_color is None:
            print("Error: Cannot get highlight_color from the cache handler")
            return False
        updateFG(image_l, highlight_color)
        return True

    def init():
        update_system_log_l("Creating cache handler")

        nonlocal cacheHandler
        cacheHandler = cM.ImageItemCacheHandler(filepaths)
        update_system_log_l("Created cache handler")

        curr = cacheHandler.curr
        if not curr:
            return
        file_l.configure(text=os.path.basename(curr.image_item.fs_item.fullName()))
        cM.initCachingForDirectory(abspath_dir, gui_is_alive_event)

    # escape keys
    ROOT.bind("<Escape>", on_escape)
    ROOT.bind("q", on_escape)

    # picture operations
    ROOT.bind("j", on_deletion)
    ROOT.bind("k", on_keep)
    ROOT.bind("c", on_clear)
    ROOT.bind("m", on_review)

    # navigation
    ROOT.bind("l", on_next)
    ROOT.bind("h", on_previous)

    # any keys
    ROOT.bind("<Key>", any_key)

    init()
    ROOT.after(50, loadImageFromCacheHandler)
    ROOT.mainloop()
    gui_is_alive_event.set()


def createImageFromAbspath(abspath: str):
    global ROOT
    img = Image.open(abspath)
    img.thumbnail(
        (ROOT.winfo_screenwidth(), ROOT.winfo_screenheight()),
        Image.Resampling.BICUBIC,
    )
    return img


def updateFG(label: ctk.CTkLabel, fg_color: int) -> bool:
    fg_color_str = COLORS.get(fg_color, IMAGE_FG_COLOR_DEFAULT)
    label.configure(fg_color=fg_color_str)
    return True
