from __future__ import annotations

import gc
import os
import subprocess
from threading import Event, Thread
from tkinter import IntVar, filedialog
from typing import Any, Callable

import customtkinter as ctk
from PIL import Image

from ..cache_management import cache_manager as cM
from ..file_system_management import file_system_manager as fsM
from ..others import others as oth
from ..shared import shared as sh


class Direction:
    left: str = "left"
    right: str = "right"
    up: str = "up"
    down: str = "down"


class Dimensions:
    def __init__(self):
        self.status_ribbon = self.StatusRibbon()
        self.general = self.General()

    class StatusRibbon:
        def __init__(self):
            self.height: int = 16
            self.label = self.Label()

        class Label:
            font_size: int = 11

    class General:
        horizontal_divider_height: int = 2


class Colors:
    def __init__(self):
        self.status = self.Status()
        self.background = self.Background()
        self.text = self.Text()
        self.palette = self.Palette()

    class Status:
        default = "white"
        keep = "green"
        delete = "red"
        to_review = "yellow"

    class Text:
        light = "#ffffff"
        light_faded = "#afafaf"
        neutral = "#e8eaed"
        neutral_faded = "#bdc1c6"
        dark_faded = "#1c1c1c"
        dark = "#111111"

    class Background:
        base = "#333333"
        lighter = "#444444"
        darker = "#2a2a2a"

    class Palette:
        secondary = "#bb9af7"
        accent = "#73daca"
        primary = "#3d59a8"
        primary_darker = "#1b3786"
        primary_lighter = "#5d79c8"


COLORS: Colors = Colors()
DIMENSIONS: Dimensions = Dimensions()
DIRECTION: Direction = Direction()


class KeyBind:
    def __init__(self, keymap: str, action: Any, desc: str | None = None):
        self.keymap: str = keymap
        self.action: Any = action
        self.desc: str | None = desc

    def getDesc(self) -> str:
        return self.desc if self.desc else "Unknown action"


class Button(ctk.CTkButton):
    def __init__(
        self,
        master: Any,
        fg_color=COLORS.palette.primary,
        hover_color=COLORS.palette.primary_lighter,
        command=None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=fg_color,
            hover_color=hover_color,
            command=command,
            **kwargs,
        )


class LabelAndValue(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        label: str,
        value: str,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.label: ctk.CTkLabel = ctk.CTkLabel(self, text=label)
        self.label.pack(side="left")

        self.value: ctk.CTkLabel = ctk.CTkLabel(self, text=value)
        self.value.pack(padx=(10, 0), anchor="w")

    def set_value(self, value: str | int):
        if type(value) is int:
            value = str(value)
        self.value.configure(text=value)


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

        self.images: list[str] = []
        self.max_image_side_length = image_size
        self.row_index = 0
        self.column_index = 0

        self.indicator: ctk.CTkLabel = ctk.CTkLabel(
            self, fg_color=indicator_color, text="", width=8, corner_radius=4
        )
        self.indicator.pack(fill=ctk.Y, side="left")

        self.title_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        self.title_frame.pack(fill=ctk.X)

        title_font = ctk.CTkFont(weight="bold", size=16)
        self.title_name: ctk.CTkLabel = ctk.CTkLabel(
            self.title_frame,
            text=title,
            font=title_font,
            anchor="w",
            justify="left",
        )
        self.title_name.pack(fill=ctk.X, side="left")

        self.title_total_images: ctk.CTkLabel = ctk.CTkLabel(
            self.title_frame,
            text="0",
            font=title_font,
            anchor="w",
            justify="right",
        )
        self.title_total_images.pack(fill=ctk.X, after=self.title_name, side="right")

        self.max_gallery_width = (
            sh.APP_WIDTH if sh.APP_WIDTH else 800 - self.indicator.winfo_width()
        )
        self.max_column = int(self.max_gallery_width / self.max_image_side_length)
        self.images_container: ctk.CTkFrame = ctk.CTkFrame(self)
        self.images_container.pack(expand=True, fill=ctk.BOTH)

    def clear_gallery(self):
        self.row_index = 0
        self.column_index = 0
        for child in self.images_container.winfo_children():
            child.destroy()
        self.images = []
        self.update_title_total_images()
        self.update_idletasks()

    def add_image(self, abspath_image: str, image: FSItemGUIHandler):
        self.images.append(abspath_image)

        self.update_title_total_images()

        image_container: ctk.CTkFrame = ctk.CTkFrame(self.images_container)
        image_item: ctk.CTkImage = ctk.CTkImage(
            image.image,
            size=get_fitted_size(
                image.image, self.max_image_side_length, self.max_image_side_length
            ),
        )
        image_view: ctk.CTkLabel = ctk.CTkLabel(
            image_container,
            text="",
            image=image_item,
            fg_color="gray",
            corner_radius=2,
        )
        image_view.pack(fill=ctk.BOTH, expand=True)

        image_position: ctk.CTkLabel = ctk.CTkLabel(
            image_view,
            text=str(len(self.images)),
            text_color="white",
            font=ctk.CTkFont(size=10, weight="bold"),
            corner_radius=12,
            height=0,
        )

        image_position.place(relx=1.0, rely=0.0, anchor="ne")

        current_row, current_col = self.row_index, self.column_index
        self.column_index = (self.column_index + 1) % self.max_column

        if self.column_index == 0:
            self.row_index += 1

        self.after_idle(
            lambda: image_container.grid(
                row=current_row, column=current_col, padx=2, pady=2, sticky="nsew"
            )
        )

    def update_title_total_images(self):
        self.title_total_images.configure(text=str(len(self.images)))
        self.update_idletasks()


class MainPopup(ctk.CTkFrame):
    def __init__(
        self,
        parent: MainApp,
        name: str = "",
        **kwargs,
    ):
        super().__init__(parent, corner_radius=16, **kwargs)
        self.app = parent
        self.name: str = name

        font = ctk.CTkFont(weight="bold", size=16)
        self.title: ctk.CTkLabel = ctk.CTkLabel(self, text=self.name, font=font)
        self.title.pack(fill=ctk.BOTH)

        ctk.CTkFrame(
            self,
            fg_color=COLORS.palette.primary,
            height=DIMENSIONS.general.horizontal_divider_height,
        ).pack(fill=ctk.X)

        self.on_close_actions: Callable[[], None] | None = None

    def set_on_close_action(self, action: Callable[[], None]):
        self.on_close_actions: Callable[[], None] | None = action

    def open(self):
        print(f"Showing popup\t{self.name}")
        self.place(
            relx=0.25,
            rely=0.25,
            relwidth=0.5,
            relheight=0.5,
        )
        self.is_shown = True

    def close(self):
        self.place_forget()
        self.is_shown = False
        self._on_close_actions()

    def _on_close_actions(self):
        if self.on_close_actions:
            self.on_close_actions()


class PositiveNegativePopup(MainPopup):
    def __init__(
        self,
        parent: MainApp,
        window_title: str,
        title: str,
        positiveText: str,
        negativeText: str,
        on_positive_action: Callable[[], None],
        on_negative_action: Callable[[], None],
        **kwargs,
    ):
        super().__init__(parent, name=window_title, **kwargs)

        self.prompt_container: ctk.CTkFrame = ctk.CTkFrame(
            self, fg_color=COLORS.background.lighter
        )
        self.prompt_container.grid_columnconfigure(index=[0, 1], weight=1)
        self.prompt_container.pack(expand=True, fill=ctk.BOTH)

        self.prompt_title: ctk.CTkLabel = ctk.CTkLabel(
            self.prompt_container, text=title
        )
        self.prompt_title.grid(row=0, column=0, columnspan=2)

        self.prompt_negative: Button = Button(
            self.prompt_container,
            text=negativeText,
            fg_color=COLORS.background.darker,
            hover_color=COLORS.background.base,
            command=self._negative,
        )
        self.prompt_negative.grid(row=1, column=0)

        self.prompt_positive: Button = Button(
            self.prompt_container, text=positiveText, command=self._positive
        )
        self.prompt_positive.grid(row=1, column=1)

        self._positive_action: Callable[[], None] = on_positive_action
        self._negative_action: Callable[[], None] = on_negative_action

        self.app.replace_keymaps(self.init_keymaps)

    def _positive(self):
        if self._positive_action:
            self._positive_action()
        self.close()

    def _negative(self):
        if self._negative_action:
            self._negative_action()
        self.close()

    def init_keymaps(self):
        self.app.bind_key(KeyBind("q", lambda event: self.close(), "Quit prompt"))
        self.app.bind_key(
            KeyBind("<Escape>", lambda event: self.close(), "Quit prompt")
        )
        self.app.bind_key(KeyBind("n", lambda event: self._negative(), "No, Cancel"))
        self.app.bind_key(KeyBind("y", lambda event: self._positive(), "Yes, Proceed"))
        self.app.bind_key(
            KeyBind("<Control-Return>", lambda event: self._positive(), "Yes, Proceed")
        )


class HelpBox(MainPopup):
    def __init__(
        self,
        app: MainApp,
        keybinds: dict[str, KeyBind],
        name: str = "Help Box",
        **kwargs,
    ):
        super().__init__(app, name, **kwargs)

        app.replace_keymaps(lambda: ())

        font = ctk.CTkFont(slant="italic", size=12)
        ctk.CTkLabel(
            self, text="Press ? to close this help box", font=font, height=0
        ).pack(fill=ctk.X, after=self.title)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill=ctk.BOTH, expand=True)

        self.container: ctk.CTkFrame = ctk.CTkFrame(
            self.scrollable_frame, fg_color=COLORS.background.lighter
        )
        self.container.pack(fill=ctk.BOTH, expand=True, padx=24, pady=8)

        for keybind in keybinds.values():
            label: LabelAndValue = LabelAndValue(
                self.container, keybind.keymap, keybind.getDesc()
            )
            label.pack(fill=ctk.X, padx=4, pady=4, ipadx=4)

        self.set_on_close_action(lambda: app.replace_keymaps_with_dict(keybinds))


class SummaryScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        start_screen: StartScreen,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.start_screen: StartScreen = start_screen
        self._filtering_by_intended_action_completed: bool = True

        # refreshing the list
        self.refresh_event: Event = Event()

        self.image_size = 128

        page_title_font = ctk.CTkFont(weight="bold", size=20)
        self.page_title_label = ctk.CTkLabel(
            self, text="Summary Page", font=page_title_font
        )
        self.page_title_label.pack(fill=ctk.X)

        self.details_container: ctk.CTkFrame = ctk.CTkFrame(self)
        self.details_container.pack(fill=ctk.X, padx=4)

        self.summary_details_jpeg_directory: LabelAndValue = LabelAndValue(
            self.details_container,
            "JPEG Directory:",
            self.start_screen.selection_jpeg.abspath_dir,
        )
        self.summary_details_jpeg_directory.pack(fill=ctk.X)

        raw_directory_path: str = (
            self.start_screen.selection_raw.abspath_dir
            if self.start_screen.selection_raw
            else "Not selected"
        )
        self.summary_details_raw_directory: LabelAndValue = LabelAndValue(
            self.details_container,
            "RAW Directory:",
            raw_directory_path,
        )
        self.summary_details_raw_directory.pack(fill=ctk.X)

        self.manage_raws: bool = start_screen.selection_raw is not None
        self.summary_details_manage_raws: LabelAndValue = LabelAndValue(
            self.details_container,
            "Manage RAWs:",
            str(self.manage_raws),
        )
        self.summary_details_manage_raws.pack(fill=ctk.X)

        self.summary_details_images_to_keep_lav: LabelAndValue = LabelAndValue(
            self.details_container, "Images to keep:", "0"
        )
        self.summary_details_images_to_keep_lav.pack(fill=ctk.X)

        self.summary_details_images_to_dump_lav: LabelAndValue = LabelAndValue(
            self.details_container, "Images to dump:", "0"
        )
        self.summary_details_images_to_dump_lav.pack(fill=ctk.X)

        self.unmarked_images: list[str] = []
        self.summary_details_unmarked_images: LabelAndValue = LabelAndValue(
            self.details_container, "Unmarked images:", str(len(self.unmarked_images))
        )
        self.summary_details_unmarked_images.pack(fill=ctk.X)

        # scrollable frame
        self.scrollable_frame_for_galleries = ctk.CTkScrollableFrame(self)
        self.scrollable_frame_for_galleries.pack(
            expand=True, fill=ctk.BOTH, padx=8, pady=8
        )

        # galleries showing intended action
        self.images_gallery_to_keep: ImageGallery = ImageGallery(
            self.scrollable_frame_for_galleries,
            "To Keep",
            COLORS.status.keep,
            image_size=self.image_size,
        )
        self.images_gallery_to_dump: ImageGallery = ImageGallery(
            self.scrollable_frame_for_galleries,
            "To Dump",
            COLORS.status.delete,
            image_size=self.image_size,
        )

        self.completion_pop_up: PositiveNegativePopup | None = None

        self.update_idletasks()

    def on_summary_screen_close(self, event):
        self.refresh_event.set()
        Thread(target=self.images_gallery_to_keep.clear_gallery, daemon=True).start()
        Thread(target=self.images_gallery_to_dump.clear_gallery, daemon=True).start()
        self.start_screen.load_page(self.start_screen.main_page)

    def init_keymaps(self):
        self.start_screen.app.bind_key(
            KeyBind("q", self.on_summary_screen_close, "Quit to Start screen")
        )
        self.start_screen.app.bind_key(
            KeyBind("<Escape>", self.on_summary_screen_close, "Quit to Start screen")
        )

        self.start_screen.app.bind_key(
            KeyBind(
                "<Control-Return>", self.prompt_for_completion, "Open completion prompt"
            )
        )

    def prompt_for_completion(self, event):
        if not self._is_filtering_by_intended_action_completed():
            print(
                "Cannot prompt for completion: Filteting by intended action is not completed yet"
            )
            return

        if self.completion_pop_up:
            print("A completion pop up already exist")
            return

        def on_close():
            print("Close")
            self.start_screen.app.replace_keymaps(self.init_keymaps)
            self.completion_pop_up = None

        def on_cancel():
            print("Cancel")
            on_close()

        def on_proceed():
            print("Proceed")

            self.start_screen.app.replace_keymaps(
                lambda: print("Removing keymaps due to processing of prompt completion")
            )
            print(f"Manage RAWs: {self.manage_raws}")

            print("JPEG to keep:")
            for image in self.images_gallery_to_keep.images:
                print(image)

            print("JPEG to dump:")
            for image in self.images_gallery_to_dump.images:
                print(image)
                get_jpeg_filename_result: fsM.FileName | None = (
                    fsM.getPartsOfNameFromAbsPath(image)
                )

                if get_jpeg_filename_result is None:
                    print("Error: Getting filename for jpeg unexpectedly returned None")
                    continue

                jpeg_filename: fsM.FileName = get_jpeg_filename_result
                image_hash = fsM.hashFile(
                    image, jpeg_filename.getFullName(force_lowercase_extension=True)
                )
                print(jpeg_filename.getFullName())

                def deleteJPEG() -> bool:
                    if not fsM.deleteFileFromAbsPath(image):
                        print(f"Error: Cannot delete jpeg: \t{image}")
                        return False
                    return True

                def deleteHashFile() -> bool:
                    abspath_cachefile = os.path.abspath(
                        os.path.join(cM.CACHE_FOLDER, image_hash)
                    )
                    print(abspath_cachefile)

                    if not fsM.deleteFileFromAbsPath(abspath_cachefile):
                        print(f"Error: Cannot delete hashfile: \t{abspath_cachefile}")
                        return False

                    return True

                def deleteRaw(selection_raw: fsM.SelectionFromDirectory) -> bool:
                    raw_filename: str = jpeg_filename.getName() + ".ARW"

                    abspath_actual_raw_file: str | None = (
                        selection_raw.is_file_in_list_by_filename(raw_filename)
                    )
                    if abspath_actual_raw_file is None:
                        print(
                            f"Did not find any matching raw file:\t{raw_filename} for image {image}"
                        )
                        return False

                    print(f"Found matching raw file:\t{raw_filename} for image {image}")

                    if not fsM.deleteFileFromAbsPath(abspath_actual_raw_file):
                        print(
                            f"Error: Cannot delete raw file: \t{abspath_actual_raw_file}"
                        )
                        return False

                    return True

                gc.collect()

                if not deleteJPEG():
                    continue

                if not deleteHashFile():
                    continue

                if self.manage_raws:
                    if self.start_screen.selection_raw is None:
                        print(
                            "Error: self.start_screen.selection_raw is unexpectedly None"
                        )
                        break
                    if not deleteRaw(self.start_screen.selection_raw):
                        continue

            on_close()
            self.after_idle(self.start_screen.app.reset)

        self.completion_pop_up = PositiveNegativePopup(
            self.start_screen.app,
            "Completion Pop Up",
            "Perform intended actions?",
            "Yes",
            "No",
            on_proceed,
            on_cancel,
        )
        self.completion_pop_up.set_on_close_action(on_close)
        self.completion_pop_up.open()

    def refresh_list(self):
        self._filtering_by_intended_action_completed = False

        self.refresh_event.set()
        self.refresh_event = Event()

        self.unmarked_images = []
        self.summary_details_images_to_keep_lav.set_value("0")
        self.summary_details_images_to_dump_lav.set_value("0")
        self.summary_details_unmarked_images.set_value("0")
        self.images_gallery_to_keep.clear_gallery()
        self.images_gallery_to_dump.clear_gallery()

        self.update_idletasks()

        for abspath_image in self.start_screen.filepaths:
            if self.refresh_event.is_set():
                return
            temp: FSItemGUIHandler | None = cM.cacheImageAtAbspathIfNotCached(
                abspath_image
            )
            if not temp:
                return
            if temp.highlight_color == COLORS.status.keep:
                self.images_gallery_to_keep.add_image(abspath_image, temp)
                self.summary_details_images_to_keep_lav.set_value(
                    len(self.images_gallery_to_keep.images)
                )
            elif temp.highlight_color == COLORS.status.delete:
                self.images_gallery_to_dump.add_image(abspath_image, temp)
                self.summary_details_images_to_dump_lav.set_value(
                    len(self.images_gallery_to_dump.images)
                )
            elif temp.highlight_color == COLORS.status.default:
                self.unmarked_images.append(abspath_image)
                self.summary_details_unmarked_images.set_value(
                    len(self.unmarked_images)
                )

        self._filtering_by_intended_action_completed = True

    def _is_filtering_by_intended_action_completed(self) -> bool:
        return self._filtering_by_intended_action_completed


class StartScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        mainApp: MainApp,
        selection_jpeg: fsM.SelectionFromDirectory,
        selection_raw: fsM.SelectionFromDirectory | None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.app: MainApp = mainApp
        self.start_screen_event: Event = Event()

        self.is_keymap_picture_actions_ready = False

        self.selection_jpeg: fsM.SelectionFromDirectory = selection_jpeg
        self.selection_raw: fsM.SelectionFromDirectory | None = selection_raw

        abspath_jpegs = self.selection_jpeg.abspath_files
        if abspath_jpegs is None:
            print("Error: jpeg_selection was empty")
            return

        self.filepaths: list[str] = abspath_jpegs
        self.filepaths_images_size = len(self.filepaths)
        self.file_counter: int = 0

        self.pages: list[ctk.CTkFrame] = []

        # pages
        self.main_page = ctk.CTkFrame(self)
        self.summary_page = ctk.CTkFrame(self)
        self.pages.append(self.main_page)
        self.pages.append(self.summary_page)

        self.load_page(self.main_page)
        self.summary_screen = SummaryScreen(self.summary_page, self)
        self.summary_screen.pack(expand=True, fill=ctk.BOTH)

        # components
        self.image_highlight_l = ctk.CTkLabel(self.main_page, text="", height=8)
        self.image_l = ctk.CTkLabel(
            self.main_page, text="", fg_color=COLORS.background.base
        )
        self.raw_file_indicator = ctk.CTkLabel(self.image_l, text="")

        self.image_highlight_l.pack(fill="x")
        self.image_l.pack(expand=True, fill=ctk.BOTH)
        self.update_idletasks()

        self.cacheHandler: cM.ImageItemCacheHandler

    def update_system_log_l(self, log: str):
        print(log)
        self.update_idletasks()

    def on_image_change(self):
        self.loadImageFromCacheHandler()

        filepath = self.cacheHandler.getAbspathOfCurrent()
        filepath = filepath if filepath else "Cannot get filepath"
        self.app.status_ribbon.filepath_section.set_filepath(filepath)
        self.app.status_ribbon.file_counter_section.set_counter(self.file_counter)

    def on_previous(self, event):
        self.update_system_log_l("Displaying previous image")

        if self.cacheHandler.prev():
            self.file_counter = self.file_counter - 1
            self.on_image_change()

    def on_next(self, event):
        self.update_system_log_l("Displaying next image")

        if self.cacheHandler.next():
            self.file_counter = self.file_counter + 1
            self.on_image_change()

    def on_deletion(self, event):
        self.update_system_log_l("Deleting")

        fg_color = COLORS.status.delete
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_keep(self, event):
        self.update_system_log_l("Keep")

        fg_color = COLORS.status.keep
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_clear(self, event):
        self.update_system_log_l("Clear")

        fg_color = COLORS.status.default
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_review(self, event):
        self.update_system_log_l("Review")

        fg_color = COLORS.status.to_review
        if not self.cacheHandler.updateHighlightColor(fg_color):
            return

        updateFG(self.image_highlight_l, fg_color)

    def on_open_image(self, event, abspath: str | None):
        if abspath is None:
            print("Cannot open image: Abspath was None")
            return
        Thread(target=lambda: os.startfile(abspath), daemon=True).start()

    def on_open_image_in_fs(self, event, abspath: str | None):
        if abspath is None:
            print("Cannot open image in File System: Abspath was None")
            return
        Thread(
            target=lambda: subprocess.run(["explorer", "/select,", abspath]),
            daemon=True,
        ).start()

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

        if self.selection_raw:
            filename: str = self.cacheHandler.getFileNameOnlyFromCurr() + ".ARW"
            if self.selection_raw.is_file_in_list_by_filename(filename):
                self.raw_file_indicator.place_forget()
            else:
                self.raw_file_indicator.place(relwidth=0.15, relheight=0.05)
            self.raw_file_indicator.configure(
                fg_color="red", text="Found no matching RAW file"
            )

        return True

    def init(self):
        self.image_l.configure(text="Loading Images", image="")
        self.update_system_log_l("Loading Images")
        self.cacheHandler = cM.ImageItemCacheHandler(self.filepaths)
        self.update_system_log_l("Created cache handler")

        curr = self.cacheHandler.curr
        if not curr:
            return

        self.file_counter = self.file_counter + 1

        cM.initCachingForDirectory(
            self.selection_jpeg.abspath_dir,
            self.app.live_event,
            self.start_screen_event,
        )
        self.app.status_ribbon.file_counter_section.set_max(len(self.filepaths))
        self.on_image_change()
        self.is_keymap_picture_actions_ready = True
        self._init_keymaps_picture_actions()

    def init_keymaps(self):
        self.app.bind_key(
            KeyBind("q", self.on_start_screen_close, "Quit to Home Screen")
        )
        self.app.bind_key(
            KeyBind("<Escape>", self.on_start_screen_close, "Quit to Home Screen")
        )

        if self.is_keymap_picture_actions_ready:
            self._init_keymaps_picture_actions()

    def _init_keymaps_picture_actions(self):
        # picture operations
        # navigation
        self.app.bind_key(KeyBind("l", self.on_next, "Move right"))
        self.app.bind_key(KeyBind("h", self.on_previous, "Move left"))

        self.app.bind_key(KeyBind("j", self.on_deletion, "Mark for deletion"))
        self.app.bind_key(KeyBind("k", self.on_keep, "Mark for keeping"))
        self.app.bind_key(KeyBind("c", self.on_clear, "Clear marks"))
        self.app.bind_key(KeyBind("m", self.on_review, "Mark for Review"))
        self.app.bind_key(
            KeyBind(
                "o",
                lambda event: self.on_open_image(
                    event, self.cacheHandler.getAbspathOfCurrent()
                ),
                "Open image in default application",
            )
        )
        self.app.bind_key(
            KeyBind(
                "e",
                lambda event: self.on_open_image_in_fs(
                    event, self.cacheHandler.getAbspathOfCurrent()
                ),
                "Open image in default file explorer",
            )
        )

        # modes
        self.app.bind_key(
            KeyBind(
                "I",
                self.on_enter_inspect_mode,
                "Enter into inspect mode",
            )
        )

        # app operations
        self.app.bind_key(
            KeyBind(
                "<Control-Return>",
                lambda event: self.load_page(self.summary_page),
                "Enter into summary page",
            )
        )

    def on_enter_inspect_mode(self, event):
        abspath_curr_image = self.cacheHandler.getAbspathOfCurrent()
        if abspath_curr_image is None:
            print("Error: Cannot get abspath of current image from cache handler")
            return

        self.app.clear_keymaps()

        self.image_l.pack_forget()
        self.image_highlight_l.pack_forget()

        self.inspect_mode: InspectMode = InspectMode(
            self.app, self.main_page, self.on_exit_inspect_mode
        )
        self.inspect_mode.set_images_to_inspect([abspath_curr_image])
        self.inspect_mode.enter()

    def on_exit_inspect_mode(self):
        self.app.status_ribbon.phase_section.set_phase("Start Screen")

        self.image_highlight_l.pack(expand=True, fill=ctk.X)
        self.image_l.pack(expand=True, fill=ctk.BOTH, after=self.image_highlight_l)

        self.app.replace_keymaps(self.init_keymaps)

    def on_start_screen_close(self, event):
        self.start_screen_event.set()
        self.app.show_home_screen()

        def hideStatusRibbonForAll():
            self.app.status_ribbon.file_counter_section.hide()
            self.app.status_ribbon.filepath_section.hide()

        hideStatusRibbonForAll()

    def load_page(self, page: ctk.CTkFrame):
        for _page in self.pages:
            _page.pack_forget()
        page.pack(expand=True, fill=ctk.BOTH)

        self.update_idletasks()

        def updateStatusRibbonForPage(page: ctk.CTkFrame):
            if page is self.main_page:
                self.app.status_ribbon.file_counter_section.show()
                self.app.status_ribbon.filepath_section.show()
            elif page is self.summary_page:
                self.app.status_ribbon.file_counter_section.hide()
                self.app.status_ribbon.filepath_section.hide()

        if page is self.main_page:
            self.app.replace_keymaps(self.init_keymaps)
            updateStatusRibbonForPage(page)
        elif page is self.summary_page:
            self.app.replace_keymaps(self.summary_screen.init_keymaps)
            updateStatusRibbonForPage(page)
            Thread(target=self.summary_screen.refresh_list, daemon=True).start()
        gc.collect()


class InspectMode:
    def __init__(self, app: MainApp, canvas_holder: ctk.CTkFrame, on_exit_action):
        self.app = app

        canvas = ctk.CTkCanvas(
            master=canvas_holder,
            width=canvas_holder.winfo_reqwidth(),
            height=canvas_holder.winfo_reqheight(),
            highlightthickness=0,
            relief="flat",
            xscrollincrement=1,
            yscrollincrement=1,
            bg=COLORS.background.base,
        )
        self.canvas_manager = self.CanvasManager(canvas, canvas_holder)
        self.canvas_manager.reset_view()
        self._on_exit_action: Callable[[], None] = on_exit_action

    def set_images_to_inspect(self, abspath_images: list[str]):
        self.canvas_manager.set_images(abspath_images)

    def enter(self):
        self.app.status_ribbon.phase_section.set_phase("Inspect")
        self.app.replace_keymaps(self.init_keymaps)
        self.on_reset_view(None)

    def on_exit(self, event=None):
        self.canvas_manager.canvas.pack_forget()
        gc.collect()
        self._on_exit_action()

    def on_zoom_in(self, event):
        self.canvas_manager.zoom_in_on_focused_image()

    def on_zoom_out(self, event):
        self.canvas_manager.zoom_out_on_focused_image()

    def on_zoom_in_and_center(self, event):
        self.on_zoom_in(None)
        self.on_center_view_to_focused_image(None)

    def on_zoom_out_and_center(self, event):
        self.on_zoom_out(None)
        self.on_center_view_to_focused_image(None)

    def on_zoom_to_fit(self, event):
        focused_image = self.canvas_manager.get_focused_image()
        if focused_image is None:
            return
        focused_image.set_zoom_to_fit()
        self.canvas_manager.render_image_on_canvas(focused_image)

    def on_zoom_fit_and_center(self, event):
        self.on_zoom_to_fit(None)
        self.on_center_view_to_focused_image(None)

    def on_pan(self, event, direction: str):
        self.canvas_manager.pan(direction)

    def on_center_view_to_focused_image(self, event):
        self.canvas_manager.center_view_to_focused_image()

    def on_reset_view(self, event):
        self.canvas_manager.reset_view()

    def init_keymaps(self):
        self.app.bind_key(KeyBind("q", self.on_zoom_out, "Zoom out"))
        self.app.bind_key(KeyBind("e", self.on_zoom_in, "Zoom in"))
        self.app.bind_key(KeyBind("f", self.on_zoom_to_fit, "Zoom fit"))
        self.app.bind_key(
            KeyBind("F", self.on_zoom_fit_and_center, "Zoom fit and center")
        )
        self.app.bind_key(
            KeyBind("Q", self.on_zoom_out_and_center, "Zoom out and center")
        )
        self.app.bind_key(
            KeyBind("E", self.on_zoom_in_and_center, "Zoom in and center")
        )
        self.app.bind_key(
            KeyBind("a", lambda event: self.on_pan(event, DIRECTION.left), "Pan left")
        )
        self.app.bind_key(
            KeyBind("d", lambda event: self.on_pan(event, DIRECTION.right), "Pan right")
        )
        self.app.bind_key(
            KeyBind("w", lambda event: self.on_pan(event, DIRECTION.up), "Pan up")
        )
        self.app.bind_key(
            KeyBind("s", lambda event: self.on_pan(event, DIRECTION.down), "Pan down")
        )
        self.app.bind_key(
            KeyBind("c", self.on_center_view_to_focused_image, "Center view to image")
        )
        self.app.bind_key(KeyBind("r", self.on_reset_view, "Reset view"))
        self.app.bind_key(KeyBind("<Escape>", self.on_exit, "Exit from inspect mode"))

    class CanvasManager:
        def __init__(self, canvas: ctk.CTkCanvas, canvas_holder: ctk.CTkFrame):
            self.canvas: ctk.CTkCanvas = canvas
            self.holder = oth.Holder(
                canvas_holder.winfo_width(),
                canvas_holder.winfo_height(),
            )

            self.panning_speed: int = 50  # in pixels
            self.images: dict[str, oth.CanvasImage] = {}
            self.focused_image_abspath: str | None = None
            self.focused_image_id: int | None = None

        def show_canvas(self):
            self.canvas.pack(fill=ctk.BOTH, expand=True)

        def reset_view(self):
            focused_image = self.get_focused_image()
            if focused_image is None:
                return

            focused_image.set_zoom_to_zoom_out_limit()

            self.render_image_on_canvas(focused_image)
            self.center_view_to_focused_image()

            self.show_canvas()

        def zoom_in_on_focused_image(self):
            focused_image = self.get_focused_image()
            if focused_image is None:
                return

            focused_image.zoom_in()
            self.render_image_on_canvas(focused_image)

        def zoom_out_on_focused_image(self):
            focused_image = self.get_focused_image()
            if focused_image is None:
                return

            focused_image.zoom_out()
            self.render_image_on_canvas(focused_image)

        def center_view_to_focused_image(self):
            focused_image = self.get_focused_image()
            if focused_image is None:
                return

            self.canvas.xview_moveto(0.0)
            self.canvas.yview_moveto(0.0)

            # centering to center of focused image
            center_of_focused = focused_image.center_of_tk_image()
            self.canvas.xview_scroll(center_of_focused.x, ctk.UNITS)
            self.canvas.yview_scroll(center_of_focused.y, ctk.UNITS)

        def pan(self, direction: str):
            x_offset = 0
            y_offset = 0
            if direction == DIRECTION.left:
                x_offset = -self.panning_speed
            elif direction == DIRECTION.right:
                x_offset = self.panning_speed
            elif direction == DIRECTION.up:
                y_offset = -self.panning_speed
            elif direction == DIRECTION.down:
                y_offset = self.panning_speed
            self.canvas.xview_scroll(x_offset, ctk.UNITS)
            self.canvas.yview_scroll(y_offset, ctk.UNITS)

        def get_focused_image(self) -> oth.CanvasImage | None:
            if not self.images:
                return None

            if self.focused_image_abspath is None:
                return None

            return self.images.get(self.focused_image_abspath)

        def clear(self):
            self.canvas.delete(ctk.ALL)

        def set_images(self, abspath_images: list[str]):
            if not abspath_images:
                print("Error: abspath_images was empty")
                return

            self.clear()
            for abspath in abspath_images:
                image_pil = Image.open(abspath)
                self.images[abspath] = oth.CanvasImage(image_pil, self.holder)

            # initial viewing behaviour
            self.focused_image_abspath = list(self.images.keys())[0]

        def render_image_on_canvas(self, image: oth.CanvasImage):
            self.clear()
            self.focused_image_id = self.canvas.create_image(
                self.holder.center_x,
                self.holder.center_y,
                anchor=ctk.CENTER,
                image=image.imageTk,
            )

            x1, y1, x2, y2 = self.canvas.bbox("all")
            padding_width = self.holder.width / 2
            padding_height = self.holder.height / 2
            scroolregion_with_padding = (
                x1 - padding_width,
                y1 - padding_height,
                x2 + padding_width,
                y2 + padding_height,
            )
            self.canvas.configure(scrollregion=scroolregion_with_padding)


class StatusRibbon(ctk.CTkFrame):
    def __init__(self, app: MainApp, **kwargs):
        super().__init__(
            app,
            fg_color=COLORS.background.darker,
            height=DIMENSIONS.status_ribbon.height,
            **kwargs,
        )
        self.app = app

        self.pack(fill=ctk.X, ipadx=24)

        self.phase_section = self.PhaseSection(self)
        self.file_counter_section = self.FileCounterSection(self)
        self.filepath_section = self.FilepathSection(self)
        self.message = self.Label(self, side=ctk.RIGHT)
        self.message.set_text("Press ? to toggle help box")

    class Label(ctk.CTkLabel):
        def __init__(
            self,
            parent: ctk.CTkFrame,
            text_color: str | None = None,
            side: str = ctk.LEFT,
            **kwargs,
        ):
            self.font = ctk.CTkFont(size=DIMENSIONS.status_ribbon.label.font_size)

            super().__init__(
                parent,
                text="",
                text_color=text_color if text_color else COLORS.text.light_faded,
                font=self.font,
                **kwargs,
            )
            self.pack(side=side, ipadx=4)

        def set_text(self, text: str):
            self.configure(text=text)

    class Title(Label):
        def __init__(
            self, parent: ctk.CTkFrame, text_color: str | None = None, **kwargs
        ):
            super().__init__(parent, text_color, **kwargs)
            self.font.configure(weight="bold")

    class BaseSeperator(ctk.CTkLabel):
        def __init__(self, parent: Any, **kwargs):
            super().__init__(
                parent,
                text="",
                width=8,
                height=parent.winfo_height(),
                **kwargs,
            )
            self.pack(side=ctk.LEFT)

    class BarSeperator(BaseSeperator):
        def __init__(self, parent: Any, **kwargs):
            super().__init__(parent, **kwargs)
            self.configure(text="|")

    class NavigationSeperator(BaseSeperator):
        def __init__(self, parent: Any, **kwargs):
            super().__init__(parent, **kwargs)
            self.configure(text=">")

    class Section(ctk.CTkFrame):
        def __init__(
            self, status_ribbon: StatusRibbon, fg_color=COLORS.background.base, **kwargs
        ):
            super().__init__(
                status_ribbon,
                fg_color=fg_color,
                height=status_ribbon.winfo_height(),
                **kwargs,
            )
            self.show()

        def show(self):
            self.pack(side=ctk.LEFT, ipadx=2)

        def hide(self):
            self.pack_forget()

    class PhaseSection(Section):
        def __init__(self, status_ribbon: StatusRibbon):
            super().__init__(status_ribbon, fg_color=COLORS.palette.primary)
            self.title = status_ribbon.Title(self, text_color=COLORS.text.neutral_faded)

        def set_phase(self, phase: str):
            self.title.set_text(phase)

    class FilepathSection(Section):
        def __init__(self, status_ribbon: StatusRibbon):
            super().__init__(status_ribbon, fg_color=COLORS.palette.secondary)
            self.filepath = status_ribbon.Label(self, text_color=COLORS.text.dark_faded)

        def set_filepath(self, filepath: str):
            self.filepath.set_text(filepath)

    class FileCounterSection(Section):
        def __init__(
            self, status_ribbon: StatusRibbon, start: int = 0, maximum: int = 0
        ):
            super().__init__(status_ribbon, fg_color=COLORS.palette.secondary)
            self.counter: int = start
            self.maximum: int = maximum

            self.counter_label = status_ribbon.Label(
                self, text_color=COLORS.text.dark_faded
            )

        def set_counter(self, counter: int):
            self.counter = counter
            self.counter_label.set_text(f"{self.counter}/{self.maximum}")

        def set_max(self, maximum: int):
            self.maximum = maximum


class MainApp(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.live_event: Event = Event()

        self.attributes("-fullscreen", True)
        self.title("Vim Photo Manager")

        self.bounded_keys: dict[str, KeyBind] = {}

        self.home_screen: HomeScreen | None = None
        self.start_screen: StartScreen | None = None

        self.working_area: ctk.CTkFrame = ctk.CTkFrame(self)
        self.working_area.pack(fill=ctk.BOTH, expand=True)

        self.status_ribbon: StatusRibbon = StatusRibbon(self)

        self.kb_help: KeyBind = KeyBind(
            "<question>", self.on_toggle_help, "Show help box"
        )
        self.bind(self.kb_help.keymap, self.kb_help.action)
        self.help_dialog: HelpBox | None = None

        self.bind("<Key>", self.unmapped_key)

        self.reset()

    def unmapped_key(self, event):
        char = event.char
        keysym = event.keysym
        print(f"Pressing unknown key:\t{char}\t{keysym}")

    def on_toggle_help(self, event=None):
        # toggling it off
        if self.help_dialog:
            self.help_dialog.close()
            self.help_dialog.destroy()
            self.help_dialog = None

        # toggling it on
        else:
            self.help_dialog = HelpBox(self, self.bounded_keys)
            self.help_dialog.open()

        print(f"Toggling help: {self.help_dialog is not None}")

    def reset(self):
        print("\n\n\t\t------------- RESETTING -------------\n\n")
        gc.collect()
        self.clear_keymaps()

        if self.help_dialog:
            self.help_dialog.close()
            self.help_dialog.destroy()
            self.help_dialog = None

        if self.home_screen:
            self.home_screen.destroy()
        self.home_screen = HomeScreen(self.working_area, self)

        if self.start_screen:
            self.start_screen.destroy()
        self.start_screen = None

        self.show_home_screen()
        self.status_ribbon.filepath_section.hide()
        self.status_ribbon.file_counter_section.hide()

    def start(self):
        if self.home_screen is None:
            print("Error: Cannot start, home_screen was unexpectedly None")
            return

        if not self.home_screen.are_directories_and_filepaths_valid():
            print("Directories or filepaths were not valid")
            return

        if self.home_screen.directory_prompt_jpeg.selection is None:
            print("Selection for jpegs was not set")
            return

        self.start_screen = StartScreen(
            self.working_area,
            self,
            selection_jpeg=self.home_screen.directory_prompt_jpeg.selection,
            selection_raw=self.home_screen.directory_prompt_raw.selection,
        )
        self.after_idle(self.start_screen.init)
        self.show_start_screen()

    def show_start_screen(self) -> bool:
        if self.home_screen is None:
            print("Error: Cannot show start screen, home_screen was unexpectedly None")
            return False

        self.home_screen.pack_forget()

        if not self.start_screen:
            print("Error: Cannot show start screen. start_screen is None")
            return False

        self.start_screen.pack(expand=True, fill=ctk.BOTH)
        self.replace_keymaps(self.start_screen.init_keymaps)
        self.status_ribbon.phase_section.set_phase("Start Screen")
        return True

    def show_home_screen(self):
        if self.start_screen:
            self.start_screen.pack_forget()

        if self.home_screen is None:
            print("Error: Cannot show home screen, home_screen was unexpectedly None")
            return

        self.home_screen.pack(expand=True, fill=ctk.BOTH)

        self.replace_keymaps(self.home_screen.init_keymaps)

        self.status_ribbon.phase_section.set_phase("Home Screen")

    def on_app_close(self, event):
        self.quit()

    def clear_keymaps(self):
        for keybind in self.bounded_keys.values():
            print(f"Unbinding:\t{keybind.keymap}\t{keybind.getDesc()}")
            self.unbind(keybind.keymap)

        self.bounded_keys = {}

    def replace_keymaps(self, keymaps_func):
        self.clear_keymaps()
        print(f"Replacing with keymaps:\t{keymaps_func}")
        keymaps_func()

    def replace_keymaps_with_dict(self, bounded_keys: dict[str, KeyBind]):
        self.clear_keymaps()
        for bounded_key in bounded_keys.values():
            self.bind_key(bounded_key)

    def bind_key(self, kb: KeyBind) -> bool:
        if self.bounded_keys.get(kb.keymap):
            print(
                f"Error: Found conflicting keys {kb.keymap}, that performs action: {kb.getDesc()}"
            )
            return False

        if kb.keymap == self.kb_help.keymap:
            print(
                f"Error: Cannot override the help keymapping, conflicting key {kb.keymap} for action: {kb.getDesc()}"
            )
            return False

        self.bind(kb.keymap, kb.action)
        self.bounded_keys[kb.keymap] = kb
        print(f"Binding:\t{kb.keymap}\t{kb.getDesc()}")
        return True


class DirectoryPromptItem(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        title: str,
        file_formats: list[str],
        on_success_event: Callable[[], None] | None = None,
        on_failure_event: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.title: str = title
        self.file_formats = file_formats
        self.selection: fsM.SelectionFromDirectory | None = None

        self.btn_directory = Button(
            self, text=self.title, command=self.select_directory
        )
        self.btn_directory.pack()

        self.result_l = ctk.CTkLabel(self, text="", text_color="red")

        # events
        self.on_success_event: Callable[[], None] | None = on_success_event
        self.on_failure_event: Callable[[], None] | None = on_failure_event

    def select_directory(self, directory: str | None = None) -> bool:
        if directory is None:
            selected_directory = filedialog.askdirectory(title=self.title, parent=self)
            if not selected_directory:
                return False
        else:
            selected_directory = directory

        self.btn_directory.configure(text=selected_directory)

        if not fsM.isDirValid(selected_directory):
            self._set_result_text("Invalid directory")
            self._failure()
            return False

        self.selection = fsM.SelectionFromDirectory(
            selected_directory, self.file_formats
        )

        if self.selection.abspath_files is None:
            self._set_result_text(
                f"Can't get filepaths at {self.selection.abspath_dir}"
            )
            self.btn_directory.configure(text=selected_directory)
            self._failure()
            return False

        if len(self.selection.abspath_files) == 0:
            self._set_result_text(
                f"No images of type {', '.join(self.selection.file_formats)} was found"
            )
            self.btn_directory.configure(text=self.selection.abspath_dir)
            self._failure()
            return False

        self.result_l.pack_forget()
        self._success()
        return True

    def _set_result_text(self, text: str):
        print(text)
        if not self.result_l.winfo_ismapped():
            self.result_l.pack()
        self.result_l.configure(text=text)

    def _success(self):
        if self.on_success_event:
            self.on_success_event()

    def _failure(self):
        if self.on_failure_event:
            self.on_failure_event()


class HomeScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        mainApp: MainApp,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.app: MainApp = mainApp

        self.set_directories_label = ctk.CTkLabel(self, text="Set directories/folder")
        self.set_directories_label.pack(pady=8)

        self.directory_prompt_jpeg: DirectoryPromptItem = DirectoryPromptItem(
            self,
            title="Choose pictures directory/folder",
            file_formats=fsM.IMAGE_EXTENSIONS,
            on_success_event=lambda: self.on_success_directory_prompt_jpeg(),
            on_failure_event=lambda: self.on_failure_directory_prompt_jpeg(),
        )
        self.directory_prompt_jpeg.pack()

        self.manage_raws_container: ctk.CTkFrame = ctk.CTkFrame(self)

        self.manage_raws_result: IntVar = IntVar(value=1)
        self.manage_raws_checkbox = ctk.CTkCheckBox(
            self.manage_raws_container,
            text="Manage RAW files too",
            variable=self.manage_raws_result,
            command=self.on_manage_raws_change,
            checkbox_width=16,
            checkbox_height=16,
            border_width=1,
        )
        self.manage_raws_checkbox.pack(padx=8, pady=8)

        self.raw_directory_container: ctk.CTkFrame = ctk.CTkFrame(
            self.manage_raws_container
        )
        self.raw_directory_container.pack(padx=8, pady=8)

        self.directory_raw_in_same_directory_result: IntVar = IntVar(value=1)
        self.directory_raw_in_same_directory = ctk.CTkCheckBox(
            self.raw_directory_container,
            text="RAW files exists in the same folder",
            variable=self.directory_raw_in_same_directory_result,
            command=self.on_directory_raw_in_same_directory_change,
            checkbox_width=16,
            checkbox_height=16,
            border_width=1,
        )
        self.directory_raw_in_same_directory.pack()

        self.directory_prompt_raw: DirectoryPromptItem = DirectoryPromptItem(
            self.raw_directory_container,
            file_formats=fsM.RAW_EXTENSIONS,
            title="Choose RAW directory/folder",
            on_success_event=lambda: self.on_success_directory_prompt_raw(),
            on_failure_event=lambda: self.on_failure_directory_prompt_raw(),
        )

        self.container = ctk.CTkFrame(self)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.pack(expand=True)

        start_font = ctk.CTkFont(weight="bold", size=16)
        self.btn_start = Button(
            self.container, text="START", command=lambda: self.start(), font=start_font
        )
        self.btn_start.grid(row=0, column=0, ipadx=40, ipady=12)

        self.log_label = ctk.CTkLabel(self.container, text="", text_color="red")

    def start(self):
        if not self.are_directories_and_filepaths_valid():
            return

        self.set_log("")
        self.app.start()
        self.pack_forget()

    def set_log(self, text: str):
        print(text)
        self.after_idle(lambda: self.log_label.configure(text=text))
        if not text:
            self.log_label.pack_forget()
        else:
            self.log_label.grid(row=1, column=0, ipadx=40, ipady=12)

    def init_keymaps(self):
        # escape keys
        self.app.bind_key(
            KeyBind("<Escape>", self.app.on_app_close, "Quit application")
        )
        self.app.bind_key(KeyBind("q", self.app.on_app_close, "Quit application"))

        # actions
        self.app.bind_key(
            KeyBind(
                "<Control-o>",
                lambda event: self.directory_prompt_jpeg.select_directory(),
                "Open JPEG directory",
            )
        )
        self.app.bind_key(
            KeyBind("<Control-Return>", lambda event: self.start(), "Start")
        )
        self.app.bind_key(
            KeyBind("<Control-R>", lambda event: self.app.reset(), "Reset")
        )

    def on_success_directory_prompt_jpeg(self):
        self.manage_raws_container.pack(after=self.directory_prompt_jpeg)

    def on_failure_directory_prompt_jpeg(self):
        self.manage_raws_container.pack_forget()

    def on_success_directory_prompt_raw(self):
        pass

    def on_failure_directory_prompt_raw(self):
        pass

    def on_manage_raws_change(self):
        if not self.expect_manage_raws():
            self.raw_directory_container.pack_forget()
            return
        self.raw_directory_container.pack(padx=8, pady=8)

    def on_directory_raw_in_same_directory_change(self):
        if self.expect_raws_in_same_directory_as_jpeg():
            self.directory_prompt_raw.pack_forget()
            return
        self.directory_prompt_raw.pack(after=self.directory_raw_in_same_directory)

    def are_directories_and_filepaths_valid(self) -> bool:
        if self.directory_prompt_jpeg.selection is None:
            self.set_log("Directory for JPEG's selection was null")
            return False

        if not self.directory_prompt_jpeg.selection.abspath_files:
            self.set_log("No jpeg files in the selected directory")
            return False

        if not self.expect_manage_raws():
            self.directory_prompt_raw.selection = None
            return True

        if self.expect_raws_in_same_directory_as_jpeg():
            if self.directory_prompt_raw.select_directory(
                self.directory_prompt_jpeg.selection.abspath_dir
            ):
                return True

            self.set_log("Directory for raw files was invalid")
            return False

        if self.directory_prompt_raw.selection is None:
            self.set_log(
                "Error: Raw selection was unexpectedly Null\nYou may have not set the RAW directory yet"
            )
            return False

        if not self.directory_prompt_raw.selection.abspath_files:
            self.set_log("No raw files in the selected directory")
            return False

        self.set_log("")

        return True

    def expect_raws_in_same_directory_as_jpeg(self) -> bool:
        return self.directory_raw_in_same_directory_result.get() == 1

    def expect_manage_raws(self) -> bool:
        return self.manage_raws_result.get() == 1


class FSItemGUIHandler:
    def __init__(self, fs_item: fsM.FileSystemItem, image):
        self.image = image
        self.highlight_color: str = COLORS.status.default
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
        Image.Resampling.BOX,
    )
    return img


def updateFG(label: ctk.CTkLabel, fg_color: str) -> bool:
    label.configure(fg_color=fg_color)
    return True


def get_fitted_size(img: Image.Image, max_w: int, max_h: int):
    orig_w, orig_h = img.size
    ratio = min(max_w / orig_w, max_h / orig_h)
    return int(orig_w * ratio), int(orig_h * ratio)
