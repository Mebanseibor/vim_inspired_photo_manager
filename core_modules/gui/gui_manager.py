from __future__ import annotations

import os
from threading import Event, Thread
from tkinter import IntVar, filedialog
from typing import Any, Callable

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


class ImageGallery(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        title: str,
        indicator_color: str,
        image_size: int,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.pack(fill=ctk.X)

        self.image_size = image_size
        self.row_index = 0
        self.column_index = 0

        self.indicator: ctk.CTkLabel = ctk.CTkLabel(
            self, fg_color=indicator_color, text="", width=8, corner_radius=4
        )
        self.indicator.pack(fill=ctk.Y, side="left")

        title_font = ctk.CTkFont(weight="bold", size=16)
        self.title: ctk.CTkLabel = ctk.CTkLabel(
            self,
            text=title,
            font=title_font,
            anchor="w",
            justify="left",
        )
        self.title.pack(fill=ctk.X)

        self.max_gallery_width = (
            sh.APP_WIDTH if sh.APP_WIDTH else 800 - self.indicator.winfo_width()
        )
        self.max_column = int(self.max_gallery_width / self.image_size)
        self.images_container: ctk.CTkFrame = ctk.CTkFrame(self)
        self.images_container.pack(expand=True, fill=ctk.BOTH)

    def clear_gallery(self):
        self.row_index = 0
        self.column_index = 0
        for child in self.images_container.winfo_children():
            child.destroy()
        self.update_idletasks()

    def add_image(self, image: FSItemGUIHandler):
        image_item: ctk.CTkImage = ctk.CTkImage(
            image.image,
            size=get_fitted_size(image.image, self.image_size, self.image_size),
        )
        image_view: ctk.CTkLabel = ctk.CTkLabel(
            self.images_container,
            text="",
            image=image_item,
            fg_color="gray",
            corner_radius=2,
        )

        current_row, current_col = self.row_index, self.column_index

        self.column_index = (self.column_index + 1) % self.max_column

        if self.column_index == 0:
            self.row_index += 1

        self.after_idle(
            lambda: image_view.grid(
                row=current_row, column=current_col, padx=2, pady=2, sticky="nsew"
            )
        )


class SummaryScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        start_screen: StartScreen,
        filepaths: dict[str, list[str]],
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.start_screen: StartScreen = start_screen
        self.filepaths = filepaths

        self.refresh_event: Event = Event()
        self.images_to_keep: list[str] = []
        self.images_to_dump: list[str] = []

        self.image_size = 128

        title_font = ctk.CTkFont(weight="bold", size=20)

        self.title_label = ctk.CTkLabel(self, text="Summary Page", font=title_font)
        self.title_label.pack(fill=ctk.X)

        # scrollable frame
        self.scrollable_frame_for_galleries = ctk.CTkScrollableFrame(self)
        self.scrollable_frame_for_galleries.pack(
            expand=True, fill=ctk.BOTH, padx=8, pady=8
        )

        # galleries showing intended action
        self.images_gallery_to_keep: ImageGallery = ImageGallery(
            self.scrollable_frame_for_galleries,
            "To Keep",
            COLORS[IMAGE_FG_COLOR_KEEP],
            image_size=self.image_size,
        )
        self.images_gallery_to_dump: ImageGallery = ImageGallery(
            self.scrollable_frame_for_galleries,
            "To Dump",
            COLORS[IMAGE_FG_COLOR_DELETE],
            image_size=self.image_size,
        )
        self.update_idletasks()

    def on_summary_screen_close(self, event):
        self.refresh_event.set()
        Thread(target=self.images_gallery_to_keep.clear_gallery, daemon=True).start()
        Thread(target=self.images_gallery_to_dump.clear_gallery, daemon=True).start()
        self.start_screen.load_page(self.start_screen.main_page)

    def init_keymaps(self):
        self.start_screen.app.bind_key("<Escape>", self.on_summary_screen_close)
        self.start_screen.app.bind_key("q", self.on_summary_screen_close)

    def refresh_list(self):
        self.refresh_event.set()
        self.refresh_event = Event()
        self.images_to_keep = []
        self.images_to_dump = []
        self.images_gallery_to_keep.clear_gallery()
        self.images_gallery_to_dump.clear_gallery()
        self.update_idletasks()

        for abspath_image in self.filepaths[fsM.IMAGES_ONLY_KEY]:
            if self.refresh_event.is_set():
                return
            temp: FSItemGUIHandler | None = cM.cacheImageAtAbspathIfNotCached(
                abspath_image
            )
            if not temp:
                return
            if temp.highlight_color == IMAGE_FG_COLOR_KEEP:
                self.images_to_keep.append(abspath_image)
                self.images_gallery_to_keep.add_image(temp)
            elif temp.highlight_color == IMAGE_FG_COLOR_DELETE:
                self.images_to_dump.append(abspath_image)
                self.images_gallery_to_dump.add_image(temp)


class StartScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: MainApp,
        directory: str,
        filepaths: dict[str, list[str]],
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.app: MainApp = parent
        self.start_screen_event: Event = Event()

        self.is_keymap_picture_actions_ready = False

        self.directory = directory
        self.filepaths = filepaths
        self.filepaths_images_size = len(filepaths.get(fsM.IMAGES_ONLY_KEY, []))

        self.pages: list[ctk.CTkFrame] = []

        # pages
        self.main_page = ctk.CTkFrame(self)
        self.summary_page = ctk.CTkFrame(self)
        self.pages.append(self.main_page)
        self.pages.append(self.summary_page)

        self.load_page(self.main_page)
        self.summary_screen = SummaryScreen(
            self.summary_page, self, filepaths=self.filepaths
        )
        self.summary_screen.pack(expand=True, fill=ctk.BOTH)

        # location section
        self.location_frame: ctk.CTkFrame = ctk.CTkFrame(self.main_page)
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
        self.mapped_key_press_l = ctk.CTkLabel(self.main_page, text="Mapped key")
        self.command_l = ctk.CTkLabel(self.main_page, text="Command")
        self.system_log_l = ctk.CTkLabel(self.main_page, text="System Logs")
        self.image_highlight_l = ctk.CTkLabel(self.main_page, text="", height=8)
        self.image_l = ctk.CTkLabel(self.main_page, text="")

        # self.command_l.pack()
        # self.mapped_key_press_l.pack()
        # self.system_log_l.pack()
        self.image_highlight_l.pack(fill="x")
        self.image_l.pack(expand=True, fill=ctk.BOTH)
        self.update_idletasks()

        if self.filepaths_images_size == 0:
            self.file_l.configure(text="No images here")

        self.cacheHandler: cM.ImageItemCacheHandler

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
        self.is_keymap_picture_actions_ready = True
        self._init_keymaps_picture_actions()

    def init_keymaps(self):
        # escape keys
        self.app.bind_key("<Escape>", self.on_start_screen_close)
        self.app.bind_key("q", self.on_start_screen_close)

        if self.is_keymap_picture_actions_ready:
            self._init_keymaps_picture_actions()

    def _init_keymaps_picture_actions(self):
        # picture operations
        self.app.bind_key("j", self.on_deletion)
        self.app.bind_key("k", self.on_keep)
        self.app.bind_key("c", self.on_clear)
        self.app.bind_key("m", self.on_review)

        # navigation
        self.app.bind_key("l", self.on_next)
        self.app.bind_key("h", self.on_previous)

        # app operations
        self.app.bind_key(
            "<Control-Return>", lambda event: self.load_page(self.summary_page)
        )

        # any keys
        self.app.bind_key("<Key>", self.any_key)

    def on_start_screen_close(self, event):
        self.start_screen_event.set()
        self.app.show_home_screen()

    def load_page(self, page: ctk.CTkFrame):
        for _page in self.pages:
            _page.pack_forget()
        page.pack(expand=True, fill=ctk.BOTH)

        self.update_idletasks()

        if page is self.main_page:
            self.app.replace_keymaps(self.init_keymaps)
        elif page is self.summary_page:
            self.app.replace_keymaps(self.summary_screen.init_keymaps)
            Thread(target=self.summary_screen.refresh_list, daemon=True).start()


class MainApp(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.live_event: Event = Event()

        self.attributes("-fullscreen", True)
        self.title("Vim Photo Manager")

        self.bounded_keys: dict[str, Any] = {}

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

        self.start_screen = StartScreen(
            self, directory=sh.BASE_ABS_PATH, filepaths=sh.BASE_FILEPATHS
        )

        self.show_start_screen()
        self.after_idle(self.start_screen.init)

    def show_start_screen(self) -> bool:
        self.home_screen.pack_forget()

        if not self.start_screen:
            print("Error: Cannot show start screen. start_screen is None")
            return False

        self.start_screen.pack(expand=True, fill=ctk.BOTH)
        self.replace_keymaps(self.start_screen.init_keymaps)
        return True

    def show_home_screen(self):
        if self.start_screen:
            self.start_screen.pack_forget()

        self.home_screen.pack(expand=True, fill=ctk.BOTH)

        self.replace_keymaps(self.home_screen.init_keymaps)

    def on_app_close(self, event):
        self.quit()

    def clear_keymaps(self):
        for key in self.bounded_keys:
            self.unbind(key)

        self.bounded_keys: dict[str, Any] = {}

    def replace_keymaps(self, keymaps_func):
        self.clear_keymaps()
        keymaps_func()

    def bind_key(self, key: str, function):
        if self.bounded_keys.get(key):
            self.unbind(key)
        self.bind(key, function)
        self.bounded_keys[key] = function


class DirectoryPromptItem(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        title: str,
        on_success_event: Callable[[], None] | None = None,
        on_failure_event: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.title: str = title
        self.directory: str = ""
        self.selfpaths: dict[str, list[str]] = {}

        self.btn_directory = ctk.CTkButton(
            self, text=self.title, command=self.select_directory
        )
        self.btn_directory.pack()

        self.result_l = ctk.CTkLabel(self, text="", text_color="red")

        # events
        self.on_success_event: Callable[[], None] | None = on_success_event
        self.on_failure_event: Callable[[], None] | None = on_failure_event

    def select_directory(self):
        directory = filedialog.askdirectory(title=self.title, parent=self)

        if not directory:
            return

        sh.BASE_ABS_PATH = None
        sh.BASE_FILEPATHS = None

        if not fsM.isDirValid(directory):
            self._set_result_text("Invalid directory")
            self.btn_directory.configure(text=self.directory)
            self._failure()
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
            self._failure()
            return

        if len(self.filepaths[fsM.IMAGES_ONLY_KEY]) == 0:
            self._set_result_text("No images was found")
            self.btn_directory.configure(text=self.directory)
            self._failure()
            return

        sh.BASE_FILEPATHS = self.filepaths

        sh.BASE_ABS_PATH = self.directory
        self.result_l.pack_forget()
        self._success()

    def _set_result_text(self, text: str):
        if not self.result_l.winfo_ismapped():
            self.result_l.pack()
        self.result_l.configure(text=text)

    def _success(self) -> None:
        if self.on_success_event:
            self.on_success_event()

    def _failure(self) -> None:
        if self.on_failure_event:
            self.on_failure_event()


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

        self.directory_prompt_jpeg: DirectoryPromptItem = DirectoryPromptItem(
            self,
            title="Choose pictures directory/folder",
            on_success_event=lambda: self.show_raw_directories_checkbox(),
            on_failure_event=lambda: self.hide_raw_directories_checkbox(),
        )
        self.directory_prompt_jpeg.pack()

        self.directory_prompt_raw: DirectoryPromptItem = DirectoryPromptItem(
            self,
            title="Choose RAW directory/folder",
        )

        self.directory_raw_in_same_directory_result: IntVar = IntVar(value=1)
        self.directory_raw_in_same_directory = ctk.CTkCheckBox(
            self,
            text="RAW files exists in the same folder",
            variable=self.directory_raw_in_same_directory_result,
            command=self.on_directory_raw_in_same_directory_change,
            checkbox_width=16,
            checkbox_height=16,
            border_width=1,
        )

        self.container = ctk.CTkFrame(self)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.pack(expand=True)

        start_font = ctk.CTkFont(weight="bold", size=16)
        self.btn_start = ctk.CTkButton(
            self.container, text="START", command=lambda: self.start(), font=start_font
        )
        self.btn_start.grid(row=0, column=0, ipadx=40, ipady=12)

        self.log_label = ctk.CTkLabel(self, text="", text_color="red")
        self.log_label.pack(after=self.container)

    def start(self):
        if sh.BASE_ABS_PATH is None:
            self.set_log("Base directory was not set")
            return
        self.set_log("")
        self.app.start()
        self.pack_forget()

    def set_log(self, text: str):
        self.after_idle(lambda: self.log_label.configure(text=text))

    def select_directory(self):
        self.directory_prompt_jpeg.select_directory()

    def init_keymaps(self):
        # escape keys
        self.app.bind("<Escape>", self.app.on_app_close)
        self.app.bind("q", self.app.on_app_close)

        # actions
        self.app.bind("<Control-o>", lambda event: self.select_directory())
        self.app.bind("<Control-Return>", lambda event: self.start())

    def show_raw_directories_checkbox(self):
        self.directory_raw_in_same_directory.pack(
            after=self.directory_prompt_jpeg, pady=(10, 0)
        )

    def hide_raw_directories_checkbox(self):
        self.directory_raw_in_same_directory.pack_forget()

    def on_directory_raw_in_same_directory_change(self):
        if self.directory_raw_in_same_directory_result.get():
            self.directory_prompt_raw.pack_forget()
            return
        self.directory_prompt_raw.pack(after=self.directory_raw_in_same_directory)


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


def get_fitted_size(img: Image.Image, max_w: int, max_h: int):
    orig_w, orig_h = img.size
    ratio = min(max_w / orig_w, max_h / orig_h)
    return int(orig_w * ratio), int(orig_h * ratio)
