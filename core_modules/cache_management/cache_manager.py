import os
import pickle
import threading as t
from PIL import Image

from ..file_system_management import file_system_manager as fsM
from ..gui import gui_manager as guiM

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


class ImageItemCacheHandler:
    def __init__(self, abspaths_images: list[str]):
        print("Creating image item cache handler")
        self.curr: ImageCacheItem | None = None
        self.head: ImageCacheItem | None = None
        self.tail: ImageCacheItem | None = None
        self.abspaths_images: list[str] = abspaths_images
        self.index_curr_ref: int | None = 0 if len(self.abspaths_images) else None
        self.size_left: int = 0
        self.size_right: int = 0

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
            self.size_right += 1

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
        print(f"size_left:\t\t{self.size_left}")
        print(f"size_right:\t\t{self.size_right}")

        pointer: ImageCacheItem | None = self.head
        pointer_size_index = -self.size_left
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

        index_next_abspath_fs_item = self.index_curr_ref + self.size_right
        next_abspath_fs_item = self.getAbspathAtIndex(index_next_abspath_fs_item)
        if next_abspath_fs_item:
            self.tail.next = ImageCacheItem(next_abspath_fs_item)
            self.tail.next.prev = self.tail
            self.tail = self.tail.next

            # when left side has reached its maximum sideway range
            if self.hasLeftReachedWindowEdge():
                self.trimHead(trim_size=False)
            else:
                self.size_left += 1
            return self.curr

        if self.hasLeftReachedWindowEdge():
            self.trimHead(trim_size=False)
        else:
            self.size_left += 1
        self.size_right -= 1

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

        index_prev_abspath_fs_item = self.index_curr_ref - self.size_left
        prev_abspath_fs_item = self.getAbspathAtIndex(index_prev_abspath_fs_item)
        if prev_abspath_fs_item:
            self.head.prev = ImageCacheItem(prev_abspath_fs_item)
            self.head.prev.next = self.head
            self.head = self.head.prev

            # when right side has reached its maximum sideway range
            if self.hasRightReachedWindowEdge():
                self.trimTail(trim_size=False)
            else:
                self.size_right += 1
            return self.curr

        if self.hasRightReachedWindowEdge():
            self.trimTail(trim_size=False)
        else:
            self.size_right += 1
        self.size_left -= 1

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

    def hasRightReachedWindowEdge(self) -> bool:
        return self.size_right >= CACHE_HANDLER_WINDOW_SIZE

    def hasLeftReachedWindowEdge(self) -> bool:
        return self.size_left >= CACHE_HANDLER_WINDOW_SIZE

    def trimHead(self, trim_size: bool = True):
        print("Trimming head")
        if not self.head:
            print("Head was null")
            return
        if not self.head.next:
            print("Error: Can't trim head, next was null")
            return
        self.head = self.head.next
        self.head.prev = None
        if trim_size:
            self.size_left -= 1

    def trimTail(self, trim_size: bool = True):
        print("Trimming tail")
        if not self.tail:
            print("Tail was null")
            return
        if not self.tail.prev:
            print("Error: Can't trim tail, prev was null")
            return
        self.tail = self.tail.prev
        self.tail.next = None
        if trim_size:
            self.size_right -= 1

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


def initCachingForDirectory(abspath_dir: str, gui_event: t.Event, start_event: t.Event):
    print("Caching directory: Started")

    def multi_threaded_caching():
        filepaths = os.listdir(abspath_dir)
        abspaths = []

        for filepath in filepaths:
            abspath = os.path.abspath(os.path.join(abspath_dir, filepath))
            if fsM.isFileOfFileTypes_fromAbspath(abspath, fsM.IMAGE_EXTENSIONS):
                abspaths.append(abspath)

        sem = t.Semaphore(2)

        def task(abspath: str):
            cacheImageAtAbspathIfNotCached(abspath)
            sem.release()

        for abspath in abspaths:
            if sem.acquire():
                if gui_event.is_set() or start_event.is_set():
                    return
                t.Thread(target=task, args=(abspath,), daemon=False).start()
        print("Caching directory: Completed")

    t.Thread(target=multi_threaded_caching, daemon=True).start()


def cacheImageAtAbspathIfNotCached(
    abspath_fs_item: str,
) -> guiM.FSItemGUIHandler | None:
    file_fullname = fsM.getFullNameFromAbspath(
        abspath_fs_item, lowercase_extension=True
    )

    if not file_fullname:
        print("file_fullname was None")
        return None

    image_hash = fsM.hashFile(abspath_fs_item, file_fullname)

    imgObj: guiM.FSItemGUIHandler | None = None

    is_image_cached: bool = isImageCached(image_hash)
    if is_image_cached:
        print(f"Getting cached image:\t{abspath_fs_item}")
        imgObj = getCachedImage(image_hash)
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
