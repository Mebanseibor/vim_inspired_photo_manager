from __future__ import annotations

import time
from enum import Enum, unique
from threading import Lock, Thread
from typing import Any, Callable, Generic, TypeVar

import customtkinter as ctk

from core_modules import gui_manager as gui

T = TypeVar("T")


@unique
class Templates(Enum):
    normal = 0
    error = 1
    warning = 2


class PlacedItemTracker:
    def __init__(self, item: ctk.CTkFrame, y_offset: int = 0, x_offset: int = 0):
        self.item: ctk.CTkFrame = item
        self.x_offset = x_offset
        self.y_offset = y_offset

    def update_y_offset(self, y_offset_diff: int):
        self.y_offset += y_offset_diff
        self.item.place(y=self.y_offset)

    def update_x_offset(self, x_offset_diff: int):
        self.x_offset += x_offset_diff
        self.item.place(x=self.x_offset)


class LinkedListNode(Generic[T]):
    def __init__(self, data: T):
        self.data: T = data
        self.next: LinkedListNode[T] | None = None


class LinkedList(Generic[T]):
    def __init__(self):
        self.head: LinkedListNode[T] | None = None
        self.tail: LinkedListNode[T] | None = None
        self._size: int = 0

    def set_on_failed_append(self, action: Callable[[], None]):
        self.append_fail_action = action

    def append(
        self,
        data: T,
        on_success: Callable[[T], None],
        on_failure: Callable[[str], None],
    ):
        new_node: LinkedListNode = LinkedListNode(data)

        if self.head is None:
            self.head = new_node
            self.tail = self.head
            self._size = 1
            on_success(data)
            return

        if self.tail is None:
            on_failure("self.tail was unexpectedly None")
            return

        self.tail.next = new_node
        self.tail = self.tail.next
        self._size += 1
        on_success(data)
        return

    def trim_head(
        self, on_success: Callable[[T], None], on_failure: Callable[[str], None]
    ):
        if self.head is None:
            on_failure("self.head was unexpectedly None")
            return None

        old_head = self.head
        self.head = self.head.next if self.head.next else None

        if self.tail == old_head:
            self.tail = None

        self._size = self._size - 1
        on_success(old_head.data)

    def get_head(self) -> T | None:
        return self.head.data if self.head else None

    def size(self) -> int:
        return self._size


class Queue(Generic[T]):
    def __init__(self):
        self.data_holder: LinkedList[T] = LinkedList[T]()

        self.enqueue_action: Callable[[T], None] | None = None
        self.dequeue_action: Callable[[T], None] | None = None
        self.enqueue_fail_action: Callable[[str], None] | None = None
        self.dequeue_fail_action: Callable[[str], None] | None = None

    def size(self) -> int:
        return self.data_holder.size()

    def enqueue(self, data: T):
        def on_success(enqueued_data: T):
            self.on_enqueue(enqueued_data)

        self.data_holder.append(data, on_success, self.on_enqueue_fail)

    def dequeue(self):
        def on_success(dequeued_data: T):
            self.on_dequeue(dequeued_data)

        self.data_holder.trim_head(on_success, self.on_dequeue_fail)

    def front(self) -> T | None:
        return self.data_holder.get_head()

    def on_enqueue_fail(self, err_msg: str):
        if self.enqueue_fail_action:
            self.enqueue_fail_action(err_msg)

    def on_dequeue_fail(self, err_msg: str):
        if self.dequeue_fail_action:
            self.dequeue_fail_action(err_msg)

    def set_on_enqueue_fail(self, action: Callable[[str], None]):
        self.dequeue_fail_action = action

    def set_on_dequeue_fail(self, action: Callable[[str], None]):
        self.dequeue_fail_action = action

    def set_on_enqueue(self, action: Callable[[T], None]):
        self.enqueue_action = action

    def set_on_dequeue(self, action: Callable[[T], None]):
        self.dequeue_action = action

    def on_enqueue(self, enqueued_data: T):
        if self.enqueue_action:
            self.enqueue_action(enqueued_data)

    def on_dequeue(self, dequeued_data: T):
        if self.dequeue_action:
            self.dequeue_action(dequeued_data)


class NotificationPanel(ctk.CTkFrame):
    def __init__(self, master: Any, app: gui.MainApp, **kwargs):
        super().__init__(master, fg_color=gui.COLORS.background.darker, **kwargs)

        self.app = app
        self.ntf_lifespan_milli: int = 5000
        self.ntf: dict[int, Notification] = {}
        self.screen_ratio_width: float = 0.2

        self.ctn_header: ctk.CTkFrame = ctk.CTkFrame(
            self, height=0, fg_color=gui.COLORS.background.darker
        )
        self.ctn_header.place(relx=0.5, relwidth=1.0, anchor=ctk.N)

        self.title: ctk.CTkLabel = ctk.CTkLabel(
            self.ctn_header, text="Notifications", font=gui.FONTS.style.title
        )
        self.title.pack(fill=ctk.X)

        self.subtitle: ctk.CTkLabel = ctk.CTkLabel(
            self.ctn_header,
            text=f"Press {self.app.kb_dismiss_ntf_panel.keymap} to dismiss panel",
            font=gui.FONTS.style.subtitle,
        )
        self.subtitle.pack(fill=ctk.X)

        self.ctn_header_seperator: ctk.CTkFrame = ctk.CTkFrame(
            self.ctn_header,
            fg_color=gui.COLORS.palette.primary_darker,
            height=gui.DIMENSIONS.general.horizontal_divider_height,
        )
        self.ctn_header_seperator.pack(fill=ctk.X)

        self.left_edge: ctk.CTkFrame = ctk.CTkFrame(
            self,
            fg_color=gui.COLORS.palette.primary_darker,
            width=gui.DIMENSIONS.general.vertical_divider_width,
        )
        self.left_edge.place(relheight=1.0)

        # on queue
        self.ntf_in_queue: Queue[int] = Queue()
        self.ntf_in_queue.set_on_enqueue(self.on_enqueue)
        self.ntf_in_queue.set_on_dequeue(self.on_dequeue)

        # on display
        self.ntf_on_display: list[PlacedItemTracker] = []
        self.ntf_on_display_occupied_height_lock: Lock = Lock()
        self.ntf_on_display_seperation: int = 4

    def show(self):
        self.place(
            relx=1.0,
            rely=1.0,
            relwidth=self.screen_ratio_width,
            relheight=1.0,
            anchor=ctk.SE,
        )
        self.lift()

    def hide(self):
        self.place_forget()

    def toggle(self):
        if self.is_showing():
            self.hide()
        else:
            self.show()

    def is_showing(self) -> bool:
        return self.winfo_ismapped()

    def ntf_in_queue_text(self) -> str:
        return str(self.ntf_in_queue.size()) + " in queue"

    def ntf_on_display_text(self) -> str:
        return str(len(self.ntf_on_display)) + " on display"

    def on_enqueue(self, ntf_id: int):
        def attempt_dequeue():
            while True:
                front_index = self.ntf_in_queue.front()

                if front_index is None:
                    return

                ntf_front = self.ntf[front_index]
                ntf_front.place(relx=1.0, rely=1.0, x=100, y=100, anchor=ctk.SE)
                ntf_front.place_forget()
                height = ntf_front.winfo_reqheight()

                ntf_display_height = (
                    self.winfo_reqheight() - self.ctn_header.winfo_height()
                )

                def front_fits() -> bool:
                    highest_height = (
                        self.ntf_on_display[0].item.winfo_y()
                        - self.ctn_header.winfo_height()
                        if self.ntf_on_display
                        else ntf_display_height
                    )
                    return highest_height - height >= 0

                self.update()

                if self.app.live_event.is_set():
                    return

                if (
                    self.ntf_on_display_occupied_height_lock.acquire_lock()
                    and front_fits()
                ):
                    self.ntf_on_display_occupied_height_lock.release_lock()
                    break
                self.ntf_on_display_occupied_height_lock.release_lock()
                time.sleep(2)

            self.ntf_in_queue.dequeue()

        Thread(target=attempt_dequeue, daemon=True).start()

    def on_dequeue(self, ntf_id: int):
        ntf = self.ntf[ntf_id]
        ntf.show()
        self.update()
        height = ntf.winfo_reqheight()
        y_offset = -(height + self.ntf_on_display_seperation)

        for item in self.ntf_on_display:
            item.update_y_offset(y_offset)

        self.ntf_on_display.append(PlacedItemTracker(ntf))
        self.update()

        self.after(
            self.ntf_lifespan_milli,
            lambda: Thread(
                target=self.consume_notification, args=(ntf_id,), daemon=True
            ).start(),
        )

    def consume_notification(self, ntf_id: int):
        oldest_item = self.ntf_on_display.pop(0)

        width = oldest_item.item.winfo_reqwidth()

        while oldest_item.x_offset <= width:
            oldest_item.update_x_offset(1)

        oldest_item.item.destroy()

        if not self.ntf_on_display:
            self.hide()

    def create_notification(
        self, ntf_id: int, message: str | int | float, template: Templates
    ):
        self.show()
        highlighter_color: str | None = None
        if template == Templates.error:
            highlighter_color = gui.COLORS.status.error
        elif template == Templates.warning:
            highlighter_color = gui.COLORS.status.warning
        else:
            highlighter_color = gui.COLORS.status.normal
        self.ntf[ntf_id] = Notification(self, ntf_id, str(message), highlighter_color)
        self.ntf_in_queue.enqueue(ntf_id)

    def queue_notification(self, id: int) -> bool:
        if self.ntf.get(id) is None:
            return False

        self.ntf_in_queue.enqueue(id)
        return True


class Notification(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        id: int,
        message: str,
        highlighter_color: str | None = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=gui.COLORS.background.darker,
            **kwargs,
        )
        self.id: int = id
        self.message: str = str(message)
        self.padding_horizontal = 12
        self.ipadding_vertical = 8

        self.highlighter: ctk.CTkFrame = ctk.CTkFrame(
            self,
            fg_color=highlighter_color,
            width=gui.DIMENSIONS.notification.highlighter_width,
            height=0,
        )
        self.highlighter.pack(fill=ctk.Y, expand=True, side=ctk.LEFT)

        content_border_width: int = 2
        self.ctn_content: ctk.CTkFrame = ctk.CTkFrame(
            self,
            border_color=gui.COLORS.background.base,
            border_width=content_border_width,
        )
        self.ctn_content.pack(
            fill=ctk.BOTH,
            expand=True,
            ipadx=self.padding_horizontal,
            ipady=self.ipadding_vertical,
        )

        self.title: ctk.CTkLabel = ctk.CTkLabel(
            self.ctn_content,
            text=self.message,
            corner_radius=8,
            fg_color=gui.COLORS.background.base,
            anchor="w",
            justify="left",
        )

        self.title.pack(
            fill=ctk.BOTH,
            expand=True,
            padx=content_border_width,
            pady=content_border_width,
        )

    def show(self):
        self.place(
            relx=1.0,
            rely=1.0,
            relwidth=1.0,
            x=gui.DIMENSIONS.general.vertical_divider_width,
            anchor=ctk.SE,
        )
        self.after_idle(
            lambda: self.title.configure(
                wraplength=self.winfo_width()
                - self.padding_horizontal
                - gui.DIMENSIONS.notification.extra_ntf_title_wrapping_offset_length
            )
        )
