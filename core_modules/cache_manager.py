from __future__ import annotations

import os
import pickle
from abc import ABC, abstractmethod
from threading import Lock, Thread
from typing import Callable

from PIL import Image

from core_modules import file_system_manager as fsM
from core_modules import gui_manager as guiM

CACHE_FOLDER = "cache"
CACHE_HANDLER_WINDOW_SIZE = 8


class ImageCacheItem:
    def __init__(self, abspath_fs_item: str):
        imgObj = cacheImageAtAbspathIfNotCached(abspath_fs_item)
        if imgObj is None:
            print(f"Error: Cannot create image_item for {abspath_fs_item}")
            return
        self.image_item: guiM.FSItemGUIHandler = imgObj
        self.next: ImageCacheItem | None = None
        self.prev: ImageCacheItem | None = None


class IndexAbspathPair:
    def __init__(self, index: int, abspath: str):
        self.index: int = index
        self.abspath: str = abspath


class ImageItemCacheHeap(ABC):
    def __init__(self, cache_handler: ImageItemCacheHandler):
        self.data_holder: list[IndexAbspathPair] = []

        self.cache_handler: ImageItemCacheHandler = cache_handler
        self.cacher: Lock = Lock()
        self.data_lock: Lock = Lock()

    def insert(self, index: int, abspath: str):
        Thread(
            target=self.cache_or_utilize_cache,
            args=(IndexAbspathPair(index, abspath),),
            daemon=True,
        ).start()

    def swap_at_pos(self, parent_pos: int, child_pos: int):
        temp = self.data_holder[parent_pos - 1]
        self.data_holder[parent_pos - 1] = self.data_holder[child_pos - 1]
        self.data_holder[child_pos - 1] = temp

    def heapify(self):
        child_pos = self.size()

        while child_pos:
            parent_pos = int(child_pos / 2)

            if self.is_parent_of_child_valid(parent_pos, child_pos):
                break

            self.swap_at_pos(parent_pos, child_pos)

            child_pos = parent_pos

    def heapify_down(self):
        root_pos = 1
        child_l_pos = root_pos * 2
        child_r_pos = root_pos * 2 + 1

        while root_pos <= self.size():
            better_pos = root_pos

            if child_l_pos <= self.size() and self.is_node_better_than_node(
                child_l_pos, better_pos
            ):
                better_pos = child_l_pos

            if child_r_pos <= self.size() and self.is_node_better_than_node(
                child_r_pos, better_pos
            ):
                better_pos = child_r_pos

            if better_pos == root_pos:
                break

            self.swap_at_pos(root_pos, better_pos)
            root_pos = better_pos
            child_l_pos = root_pos * 2
            child_r_pos = root_pos * 2 + 1

    @abstractmethod
    def type(self) -> str:
        pass

    @abstractmethod
    def is_node_better_than_node(self, node_a_pos: int, node_b_pos: int) -> bool:
        pass

    @abstractmethod
    def is_parent_of_child_valid(self, parent_pos: int, child_pos: int) -> bool:
        pass

    def display_values(self):
        values = ""
        for data in self.data_holder:
            values += str(data.index) + ", "
        print(f"{self.type()}:\t{values}")

    def cache_or_utilize_cache(self, item: IndexAbspathPair):
        if self.data_lock.acquire_lock():
            print("Lock acquired: before insertion")
            self.data_holder.append(item)
            self.heapify()
            print("Lock released: after insertion")
            self.data_lock.release_lock()

        if self.cacher.acquire_lock(blocking=False):
            while self.data_holder:
                root: IndexAbspathPair | None = self.extract()

                if root is None:
                    print("Error: Root was unexpectedly None")
                    self.cacher.release_lock()
                    return

                loop_lock: Lock = Lock()
                loop_lock.acquire_lock()
                print(f"{self.type()}, lock_lock acquired")

                def on_failure(err_msg: str):
                    print(f"Error: {err_msg}")
                    print(f"{self.type()}, lock_lock released")
                    loop_lock.release_lock()
                    return

                def on_success(
                    root: IndexAbspathPair, is_item_still_within_window_bounds: bool
                ):
                    if not is_item_still_within_window_bounds:
                        print(f"{self.type()}, lock_lock released")
                        loop_lock.release_lock()
                        return

                    cached_image: ImageCacheItem = ImageCacheItem(root.abspath)

                    index_in_demand: int | None = self.index_in_demand()

                    if index_in_demand is None:
                        print(f"{self.type()}, no index in demand")
                        print(f"{self.type()}, lock_lock released")
                        loop_lock.release()
                        return

                    if root.index != index_in_demand:
                        print(f"{self.type()}, lock_lock released")
                        loop_lock.release_lock()
                        return

                    def on_complete():
                        self.cache_handler.displayDetailsCacheItem(
                            self.cache_handler.tail
                        )
                        print(f"{self.type()}, lock_lock released")
                        loop_lock.release_lock()

                    self.attach_to_window(cached_image, on_complete)

                self.check_valid_to_extend_ends(root, on_success, on_failure)
                loop_lock.acquire_lock()

            self.cacher.release_lock()

    def check_valid_to_extend_ends(
        self,
        item: IndexAbspathPair,
        on_success: Callable[[IndexAbspathPair, bool], None],
        on_failure: Callable[[str], None],
    ):
        curr_index: int | None = self.cache_handler.index_curr_ref
        size: int = self.get_window_size_end_wise()
        furthest_required_end_offset: int = self.furthest_required_end_offset(size)

        if curr_index is None:
            on_failure("Cache_handler's index curr ref was unexpectedly None")
            return

        is_item_still_within_window_bounds: bool = self.is_index_within_window_bounds(
            curr_index + furthest_required_end_offset, item.index
        )

        on_success(item, is_item_still_within_window_bounds)

    @abstractmethod
    def index_in_demand(self) -> int | None:
        pass

    @abstractmethod
    def attach_to_window(
        self, cached_image: ImageCacheItem, on_complete: Callable[[], None]
    ):
        pass

    @abstractmethod
    def is_index_within_window_bounds(self, curr: int, index: int) -> bool:
        pass

    @abstractmethod
    def get_window_size_end_wise(self) -> int:
        pass

    @abstractmethod
    def furthest_required_end_offset(self, size: int) -> int:
        pass

    def size(self) -> int:
        return len(self.data_holder)

    def extract(self) -> IndexAbspathPair | None:
        if not self.data_holder:
            return None

        if self.data_lock.acquire_lock():
            root = self.data_holder[0]

            print("Lock acquired: in extract")
            if self.size() == 1:
                self.data_holder.pop(0)
            else:
                self.data_holder[0] = self.data_holder.pop()
                self.heapify_down()
            print("Lock released: in extract")
            self.data_lock.release_lock()

            return root


class ImageItemCacheHeapHead(ImageItemCacheHeap):
    def index_in_demand(self) -> int | None:
        return self.cache_handler.in_demand_head_index()

    def type(self) -> str:
        return "Head"

    def is_node_better_than_node(self, node_a_pos: int, node_b_pos: int) -> bool:
        return (
            self.data_holder[node_a_pos - 1].index
            >= self.data_holder[node_b_pos - 1].index
        )

    def is_parent_of_child_valid(self, parent_pos: int, child_pos: int) -> bool:
        child_value = self.data_holder[child_pos - 1].index
        parent_value = self.data_holder[parent_pos - 1].index
        return parent_value >= child_value

    def attach_to_window(
        self, cached_image: ImageCacheItem, on_complete: Callable[[], None]
    ):
        if self.cache_handler.head is None:
            print("Error: Head was unexpectedly None")
            on_complete()
            return

        self.cache_handler.head.prev = cached_image
        self.cache_handler.head.prev.next = self.cache_handler.head
        self.cache_handler.head = self.cache_handler.head.prev
        on_complete()

    def is_index_within_window_bounds(self, curr: int, index: int) -> bool:
        return index >= curr

    def get_window_size_end_wise(self) -> int:
        return self.cache_handler.actual_window_size_left

    def furthest_required_end_offset(self, size: int) -> int:
        return -size


class ImageItemCacheHeapTail(ImageItemCacheHeap):
    def index_in_demand(self) -> int | None:
        return self.cache_handler.in_demand_tail_index()

    def type(self) -> str:
        return "Tail"

    def is_node_better_than_node(self, node_a_pos: int, node_b_pos: int) -> bool:
        return (
            self.data_holder[node_a_pos - 1].index
            <= self.data_holder[node_b_pos - 1].index
        )

    def is_parent_of_child_valid(self, parent_pos: int, child_pos: int) -> bool:
        child_value = self.data_holder[child_pos - 1].index
        parent_value = self.data_holder[parent_pos - 1].index
        return parent_value <= child_value

    def attach_to_window(
        self, cached_image: ImageCacheItem, on_complete: Callable[[], None]
    ):
        if self.cache_handler.tail is None:
            print("Error: Tail was unexpectedly None")
            on_complete()
            return

        self.cache_handler.tail.next = cached_image
        self.cache_handler.tail.next.prev = self.cache_handler.tail
        self.cache_handler.tail = self.cache_handler.tail.next
        on_complete()

    def is_index_within_window_bounds(self, curr: int, index: int) -> bool:
        return index <= curr

    def get_window_size_end_wise(self) -> int:
        return self.cache_handler.actual_window_size_right

    def furthest_required_end_offset(self, size: int) -> int:
        return size


class ImageItemCacheHandler:
    def __init__(self, abspaths_images: list[str]):
        print("Creating image item cache handler")
        self.curr: ImageCacheItem | None = None
        self.head: ImageCacheItem | None = None
        self.tail: ImageCacheItem | None = None
        self.abspaths_images: list[str] = abspaths_images
        self.index_curr_ref: int | None = 0 if len(self.abspaths_images) else None
        self.actual_window_size_left: int = 0
        self.actual_window_size_right: int = 0
        self.head_heap: ImageItemCacheHeapHead = ImageItemCacheHeapHead(self)
        self.tail_heap: ImageItemCacheHeapTail = ImageItemCacheHeapTail(self)

        for i in range(min(CACHE_HANDLER_WINDOW_SIZE + 1, len(self.abspaths_images))):
            cacheItem = ImageCacheItem(self.abspaths_images[i])
            if not self.head:
                self.head = cacheItem
                self.tail = self.head
                self.curr = self.head
                continue

            if not self.tail:
                print("Error: Cannot append item, tail is null")
                continue

            self.tail.next = cacheItem
            cacheItem.prev = self.tail
            self.tail = self.tail.next
            self.actual_window_size_right += 1

    def in_demand_head_index(self) -> int | None:
        if self.curr is None or self.index_curr_ref is None:
            return None

        ptr = self.curr.prev
        count = 0

        while ptr:
            ptr = ptr.prev
            count += 1

        if count == 0 and not self.actual_window_size_left:
            return None

        if count >= self.actual_window_size_left:
            return None

        return self.index_curr_ref - count - 1

    def in_demand_tail_index(self) -> int | None:
        if self.curr is None or self.index_curr_ref is None:
            return None

        ptr = self.curr.next
        count = 0

        while ptr:
            ptr = ptr.next
            count += 1

        if count == 0 and not self.actual_window_size_right:
            return None

        if count >= self.actual_window_size_right:
            return None

        return count + self.index_curr_ref + 1

    def displayDetails(self):
        print("\n\n")

        self.displayDetailsCacheItem(self.curr)
        print("\n")

        print(
            f"head:\t\t\t{self.head.image_item.fs_item.fullName() if self.head else None}"
        )
        print(
            f"curr:\t\t\t{self.curr.image_item.fs_item.fullName() if self.curr else None}"
        )
        print(
            f"tail:\t\t\t{self.tail.image_item.fs_item.fullName() if self.tail else None}"
        )
        print(f"index_curr_ref:\t\t{self.index_curr_ref}")
        print(f"size_left:\t\t{self.actual_window_size_left}")
        print(f"size_right:\t\t{self.actual_window_size_right}")
        print(f"demanded_head_index:\t{self.in_demand_head_index()}")
        print(f"demanded_tail_index:\t{self.in_demand_tail_index()}")

        pointer: ImageCacheItem | None = self.head
        pointer_size_index = -self.actual_window_size_left
        print("abs\tcache\t\tname")
        while pointer:
            abspointer = (
                "None"
                if self.index_curr_ref is None
                else str(self.index_curr_ref + pointer_size_index)
            )
            print(
                f"{abspointer}\t{pointer_size_index}\t\t{pointer.image_item.fs_item.fullName()}"
            )
            pointer = pointer.next
            pointer_size_index += 1

    def displayDetailsCacheItem(self, cacheItem: ImageCacheItem | None = None):
        print(
            f"cacheItem:\t\t{cacheItem.image_item.fs_item.fullName() if cacheItem else None}"
        )

        cache_prev = (
            cacheItem.prev.image_item.fs_item.fullName()
            if cacheItem and cacheItem.prev
            else None
        )
        print(f"cacheItem.prev:\t\t{cache_prev}")

        cache_next = (
            cacheItem.next.image_item.fs_item.fullName()
            if cacheItem and cacheItem.next
            else None
        )
        print(f"cacheItem.next:\t\t{cache_next}")

    def next(self) -> ImageCacheItem | None:
        if (
            not self.curr
            or not self.head
            or not self.tail
            or self.index_curr_ref is None
        ):
            print("Error: Found null pointers")
            return None

        # if the next cache is not present
        if not self.curr.next:
            return None

        self.curr = self.curr.next
        self.index_curr_ref += 1

        index_next_abspath_outside_window = (
            self.index_curr_ref + self.actual_window_size_right
        )
        next_abspath_outside_window = self.getAbspathAtIndex(
            index_next_abspath_outside_window
        )
        if next_abspath_outside_window:
            self.tail_heap.insert(
                index_next_abspath_outside_window, next_abspath_outside_window
            )
        else:
            self.actual_window_size_right -= 1

        if self.actual_window_size_left < CACHE_HANDLER_WINDOW_SIZE:
            self.actual_window_size_left += 1
            return self.curr

        if not self.head.next:
            print("Error: Can't trim head, next was null")
            return
        count = 0
        ptr = self.curr
        while ptr.prev and count != CACHE_HANDLER_WINDOW_SIZE:
            count += 1
            ptr = ptr.prev

        self.head = ptr
        self.head.prev = None

        return self.curr

    def prev(self) -> ImageCacheItem | None:
        if (
            not self.curr
            or not self.head
            or not self.tail
            or self.index_curr_ref is None
        ):
            print("Error: Found null pointers")
            return None

        # if the previous cache is not present
        if not self.curr.prev:
            return None

        self.curr = self.curr.prev
        self.index_curr_ref -= 1

        index_prev_abspath_outside_window = (
            self.index_curr_ref - self.actual_window_size_left
        )
        prev_abspath_outside_window = self.getAbspathAtIndex(
            index_prev_abspath_outside_window
        )
        if prev_abspath_outside_window:
            self.head_heap.insert(
                index_prev_abspath_outside_window, prev_abspath_outside_window
            )
        else:
            self.actual_window_size_left -= 1

        if self.actual_window_size_right < CACHE_HANDLER_WINDOW_SIZE:
            self.actual_window_size_right += 1
            return self.curr

        if not self.tail.prev:
            print("Error: Can't trim tail, prev was null")
            return

        count = 0
        ptr = self.curr
        while ptr.next and count != CACHE_HANDLER_WINDOW_SIZE:
            count += 1
            ptr = ptr.next
        self.tail = ptr
        self.tail.next = None

        return self.curr

    def getAbspathAtIndex(self, index: int) -> str | None:
        print(f"Getting abspath at:\t{index}")
        return (
            self.abspaths_images[index]
            if index >= 0 and index < len(self.abspaths_images)
            else None
        )

    def getAbspathOfCurrent(self) -> str | None:
        print("Getting abspath of current")
        if self.index_curr_ref is None:
            print("Error: Index curr ref is None")
            return None
        return self.getAbspathAtIndex(self.index_curr_ref)

    def getFileFullNameFromCurr(self) -> str:
        return self.curr.image_item.fs_item.fullName() if self.curr else ""

    def getFileNameOnlyFromCurr(self) -> str:
        return self.curr.image_item.fs_item.getNameOnly() if self.curr else ""

    def updateHighlightColor(self, fg_color: str) -> bool:
        if not self.curr:
            print("Curr was unexpected Null")
            return False

        self.curr.image_item.highlight_color = fg_color
        cacheImage(self.curr.image_item)

        return True

    def getImage(self) -> Image.Image | None:
        if not self.curr:
            print("Curr was unexpected Null")
            return None

        return self.curr.image_item.image

    def getHighlightColor(self) -> str | None:
        if not self.curr:
            print("Curr was unexpected Null")
            return None

        return self.curr.image_item.highlight_color


def cacheImage(img_obj: guiM.FSItemGUIHandler, expect_no_clash: bool = False) -> bool:
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


def getCachedImage(image_hash: str) -> guiM.FSItemGUIHandler | None:
    abspath_cache = os.path.abspath(CACHE_FOLDER)
    abspath_cached_image = os.path.join(abspath_cache, image_hash)
    try:
        with open(abspath_cached_image, "rb") as file:
            imgObj = pickle.load(file)
            return imgObj
    except (pickle.UnpicklingError, EOFError):
        return None
    except OSError:
        return None


def utilize_cache(abspath: str) -> guiM.FSItemGUIHandler | None:
    file_fullname = fsM.getFullNameFromAbspath(abspath, lowercase_extension=True)

    if not file_fullname:
        print("file_fullname was None")
        return None

    image_hash = fsM.hashFile(abspath, file_fullname)

    if not isImageCached(image_hash):
        return None

    print(f"Getting cached image:\t{abspath}")
    return getCachedImage(image_hash)


def cacheImageAtAbspathIfNotCached(
    abspath_fs_item: str,
) -> guiM.FSItemGUIHandler | None:
    imgObj: guiM.FSItemGUIHandler | None = utilize_cache(abspath_fs_item)

    if imgObj is None:
        print(f"Caching image:\t{abspath_fs_item}")
        imgObj = guiM.FSItemGUIHandler(
            fsM.FileSystemItem(abspath_fs_item),
            guiM.createImageFromAbspath(abspath_fs_item),
        )
        if not cacheImage(imgObj):
            print(f"Error: Cannot cache image {abspath_fs_item}")
            return None
    return imgObj
