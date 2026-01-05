import os
import pickle

from ..gui import gui_manager as guiM
from ..shared import shared as s

CACHE_FOLDER = "cache"


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


def getCachedImage(image_hash: str):
    abspath_cache = os.path.abspath(CACHE_FOLDER)
    abspath_cached_image = os.path.join(abspath_cache, image_hash)
    with open(abspath_cached_image, "rb") as file:
        imgObj = pickle.load(file)
        return imgObj
