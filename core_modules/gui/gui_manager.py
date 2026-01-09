import os
from threading import Event
from tkinter import filedialog
from typing import Any
import customtkinter as ctk
from PIL import Image

from ..cache_management import cache_manager as cM
from ..file_system_management import file_system_manager as fsM
from ..shared import shared as sh

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


class StartScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        directory: str,
        filepaths: dict[str, list[str]],
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.app = parent
        self.start_screen_event: Event = Event()

        self.directory = directory
        self.filepaths = filepaths
        self.filepaths_images_size = len(filepaths.get(fsM.IMAGES_ONLY_KEY, []))

        # location section
        self.location_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        self.location_frame.grid_rowconfigure(0, weight=1)
        self.location_frame.grid_columnconfigure(1, weight=1)
        self.location_frame.pack(fill=ctk.X)

        self.currect_abs_path_l = ctk.CTkLabel(self.location_frame, text=directory)
        self.file_l = ctk.CTkLabel(
            self.location_frame, text=f"Number of images = {self.filepaths_images_size}"
        )

        self.currect_abs_path_l.grid(row=0, column=0)
        self.file_l.grid(row=0, column=1, sticky="w", padx=(10, 5))

        # components
        self.mapped_key_press_l = ctk.CTkLabel(self, text="Mapped key")
        self.command_l = ctk.CTkLabel(self, text="Command")
        self.system_log_l = ctk.CTkLabel(self, text="System Logs")
        self.image_highlight_l = ctk.CTkLabel(self, text="", height=8)
        self.image_l = ctk.CTkLabel(self, text="")

        # self.command_l.pack()
        # self.mapped_key_press_l.pack()
        # self.system_log_l.pack()
        self.image_highlight_l.pack(fill="x")
        self.image_l.pack(expand=True, fill=ctk.BOTH)
        self.update_idletasks()

        if self.filepaths_images_size == 0:
            self.file_l.configure(text="No images here")

        self.cacheHandler: cM.ImageItemCacheHandler

        # escape keys
        self.app.bind("<Escape>", self.on_start_screen_close)
        self.app.bind("q", self.on_start_screen_close)

    def update_system_log_l(self, log: str):
        print(log)
        self.after(0, lambda: self.system_log_l.configure(text=log))
        self.update_idletasks()

    def event_char(self, char):
        return f"'{char}'"

    def on_previous(self, event):
        self.update_system_log_l("Displaying previous image")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))

        if self.filepaths_images_size == 0:
            self.command_l.configure(text="No image")
            return

        self.cacheHandler.prev()
        self.file_l.configure(text=self.cacheHandler.getFileNameFromCurr())
        self.command_l.configure(text="Prev photo")
        self.loadImageFromCacheHandler()

    def on_next(self, event):
        self.update_system_log_l("Displaying next image")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))

        if self.filepaths_images_size == 0:
            self.command_l.configure(text="No image")
            return

        self.cacheHandler.next()
        self.file_l.configure(text=self.cacheHandler.getFileNameFromCurr())
        self.command_l.configure(text="Next photo")
        self.loadImageFromCacheHandler()

    def on_deletion(self, event):
        self.update_system_log_l("Deleting")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))
        self.command_l.configure(text="Marking to delete")

        fg_color = IMAGE_FG_COLOR_DELETE
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_keep(self, event):
        self.update_system_log_l("Keep")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))
        self.command_l.configure(text="Marking to keep")

        fg_color = IMAGE_FG_COLOR_KEEP
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_clear(self, event):
        self.update_system_log_l("Clear")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))
        self.command_l.configure(text="Marking to clear")

        fg_color = IMAGE_FG_COLOR_DEFAULT
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_review(self, event):
        self.update_system_log_l("Review")
        self.mapped_key_press_l.configure(text=self.event_char(event.char))
        self.command_l.configure(text="Marking to review")

        fg_color = IMAGE_FG_COLOR_TO_REVIEW
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def any_key(self, event):
        self.mapped_key_press_l.configure(text=self.event_char(event.char))
        self.command_l.configure(text=event.keysym)

    def loadImageFromCacheHandler(self) -> bool:
        def get_fitted_size(img, max_w, max_h):
            orig_w, orig_h = img.size
            ratio = min(max_w / orig_w, max_h / orig_h)
            return int(orig_w * ratio), int(orig_h * ratio)

        img = self.cacheHandler.getImage()

        if not img:
            self.update_system_log_l("Error: Cannot get Image of cache handler")
            return False

        photo = ctk.CTkImage(
            img,
            size=get_fitted_size(
                img, self.image_l.winfo_width(), self.image_l.winfo_height()
            ),
        )

        self.image_l.configure(text="", image=photo)
        highlight_color = self.cacheHandler.getHighlightColor()

        if highlight_color is None:
            self.update_system_log_l(
                "Error: Cannot get highlight_color from the cache handler"
            )
            return False
        updateFG(self.image_highlight_l, highlight_color)

        return True

    def init(self):
        self.image_l.configure(text="Loading Images", image="")
        self.update_system_log_l("Loading Images")
        self.cacheHandler = cM.ImageItemCacheHandler(
            self.filepaths[fsM.IMAGES_ONLY_KEY]
        )
        self.update_system_log_l("Created cache handler")

        curr = self.cacheHandler.curr
        if not curr:
            return
        self.file_l.configure(text=os.path.basename(curr.image_item.fs_item.fullName()))
        cM.initCachingForDirectory(
            self.directory, self.app.live_event, self.start_screen_event
        )
        self.loadImageFromCacheHandler()

        # picture operations
        self.app.bind("j", self.on_deletion)
        self.app.bind("k", self.on_keep)
        self.app.bind("c", self.on_clear)
        self.app.bind("m", self.on_review)

        # navigation
        self.app.bind("l", self.on_next)
        self.app.bind("h", self.on_previous)

        # any keys
        self.app.bind("<Key>", self.any_key)

    def on_start_screen_close(self, event):
        self.start_screen_event.set()
        self.app.show_home_screen()


class MainApp(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.live_event: Event = Event()

        self.attributes("-fullscreen", True)
        self.title("Vim Photo Manager")

        self.home_screen: HomeScreen = HomeScreen(self)
        self.start_screen: StartScreen | None = None

        self.show_home_screen()
        return

    def start(self):
        if sh.BASE_ABS_PATH is None:
            print("Directory was null")
            return

        if sh.BASE_FILEPATHS is None:
            print("Filepaths was null")
            return

        self.home_screen.pack_forget()

        self.start_screen = StartScreen(
            self, directory=sh.BASE_ABS_PATH, filepaths=sh.BASE_FILEPATHS
        )
        self.start_screen.pack(expand=True, fill=ctk.BOTH)
        self.after_idle(self.start_screen.init)

    def show_home_screen(self):
        if self.start_screen:
            self.start_screen.pack_forget()

        self.home_screen.pack(expand=True, fill=ctk.BOTH)

        self.home_screen.init_keymaps()

    def on_app_close(self, event):
        self.quit()


class DirectoryPromptItem(ctk.CTkFrame):
    def __init__(self, parent: Any, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.title: str = title
        self.directory: str = ""
        self.selfpaths: dict[str, list[str]] = {}

        self.btn_directory = ctk.CTkButton(
            self, text=self.title, command=self.select_directory
        )
        self.btn_directory.pack()

        self.result_l = ctk.CTkLabel(self, text="")

    def select_directory(self):
        directory = filedialog.askdirectory(title=self.title, parent=self)

        if not directory:
            return

        sh.BASE_ABS_PATH = None
        sh.BASE_FILEPATHS = None

        if not fsM.isDirValid(directory):
            self._set_result_text("Invalid directory")
            self.btn_directory.configure(text=self.directory)
            return

        self.directory = directory

        self.btn_directory.configure(text=self.directory)
        self.filepaths = fsM.getFilePathsAtAbspathForFormats(
            self.directory,
            file_formats={fsM.IMAGES_ONLY_KEY: True, fsM.RAWS_ONLY_KEY: True},
        )

        if self.filepaths is None:
            self._set_result_text("Can't get filepaths at {self.directory}")
            self.btn_directory.configure(text=self.directory)
            return

        if len(self.filepaths[fsM.IMAGES_ONLY_KEY]) == 0:
            self._set_result_text(
                f"No images was found at this directory: {self.directory}\n"
            )
            self.btn_directory.configure(text=self.directory)
            return

        sh.BASE_FILEPATHS = self.filepaths

        sh.BASE_ABS_PATH = self.directory
        self.result_l.pack_forget()

    def _set_result_text(self, text: str):
        if not self.result_l.winfo_ismapped():
            self.result_l.pack()
        self.result_l.configure(text=text)


class HomeScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.app = parent

        self.set_directories_label = ctk.CTkLabel(self, text="Set directories/folder")
        self.set_directories_label.pack(pady=8)

        self.directory_prompt: DirectoryPromptItem = DirectoryPromptItem(
            self, title="Choose pictures directory/folder"
        )
        self.directory_prompt.pack()

        self.container = ctk.CTkFrame(self)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.pack(expand=True)

        start_font = ctk.CTkFont(weight="bold", size=16)
        self.btn_start = ctk.CTkButton(
            self.container, text="START", command=lambda: self.start(), font=start_font
        )
        self.btn_start.grid(row=0, column=0, ipadx=40, ipady=12)

        self.log_label = ctk.CTkLabel(self, text="")
        self.log_label.pack(after=self.container)

    def start(self):
        if sh.BASE_ABS_PATH is None:
            self.set_log("Base directory was not set")
            return
        self.app.start()
        self.pack_forget()

    def set_log(self, text: str):
        self.after_idle(lambda: self.log_label.configure(text=text))

    def select_directory(self):
        self.directory_prompt.select_directory()

    def init_keymaps(self):
        # escape keys
        self.app.bind("<Escape>", self.app.on_app_close)
        self.app.bind("q", self.app.on_app_close)

        # actions
        self.app.bind("<Control-o>", lambda event: self.select_directory())
        self.app.bind("<Control-Return>", lambda event: self.start())


class FSItemGUIHandler:
    def __init__(self, fs_item: fsM.FileSystemItem, image):
        self.image = image
        self.highlight_color: int = IMAGE_FG_COLOR_DEFAULT
        self.fs_item: fsM.FileSystemItem = fs_item


def gui():
    app = MainApp()

    sh.APP_WIDTH = app.winfo_screenwidth()
    sh.APP_HEIGHT = app.winfo_screenheight()

    app.mainloop()
    app.live_event.set()


def createImageFromAbspath(abspath: str):
    if sh.APP_WIDTH is None or sh.APP_HEIGHT is None:
        print("App dimensions was not found")
        return

    img = Image.open(abspath)
    img.thumbnail(
        (sh.APP_WIDTH, sh.APP_HEIGHT),
        Image.Resampling.BICUBIC,
    )
    return img


def updateFG(label: ctk.CTkLabel, fg_color: int) -> bool:
    fg_color_str = COLORS.get(fg_color, IMAGE_FG_COLOR_DEFAULT)
    label.configure(fg_color=fg_color_str)
    return True
