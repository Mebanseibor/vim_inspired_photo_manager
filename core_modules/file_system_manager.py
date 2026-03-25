import gc
import stat
import os
import time
from typing import Callable

import xxhash

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
RAW_EXTENSIONS = ["arw"]

IMAGES_ONLY_KEY = "images_only"
RAWS_ONLY_KEY = "raw_files_only"


class SelectionFromDirectory:
    def __init__(self, abspath_dir: str, file_formats: list[str]):
        if not os.path.exists(abspath_dir):
            print(f"Error: Path {abspath_dir} does not exist")
            return
        self.abspath_dir: str = abspath_dir
        self.file_formats: list[str] = file_formats
        self.abspath_files: list[str] | None = self.get_files()

    def get_files(self) -> list[str] | None:
        if not os.path.exists(self.abspath_dir):
            print(f"Invalid operation: Path {self.abspath_dir} does not exist")
            return None

        self.abspath_files = []

        for filepath in os.listdir(self.abspath_dir):
            abspath_file = os.path.abspath(os.path.join(self.abspath_dir, filepath))
            if isFileOfFileTypes_fromAbspath(abspath_file, self.file_formats):
                self.abspath_files.append(abspath_file)

        return self.abspath_files

    def is_file_in_list_by_filename(self, filename: str) -> str | None:
        if self.abspath_files is None:
            print("Error: filepaths are not set yet")
            return None

        for abspath_file in self.abspath_files:
            if os.path.basename(abspath_file) == filename:
                return abspath_file
        return None


class FileSystemItem:
    def __init__(self, abspath: str):
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
            hashFile(abspath, self.fullName()) if self.is_file else None
        )

    def display_details(self):
        print(f"fullName():\t{self.fullName()}")
        print(f"is_file:\t{self.is_file}")
        print(f"is_image():\t{self.is_image()}")
        print(f"name:\t\t{self.name}")
        print(f"extension:\t{self.extension}")
        print(f"file_hash:\t{self.file_hash}")

    def fullName(self):
        name = self.name if self.name else ""
        ext = f".{self.extension}" if self.extension else ""
        return name + ext

    def getNameOnly(self):
        return self.name if self.name else ""

    def is_image(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        return self.extension in IMAGE_EXTENSIONS

    def is_raw(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        return self.extension in RAW_EXTENSIONS


class FileName:
    def __init__(self, name: str | None, extension: str | None):
        self.name: str | None = name
        self.extension: str | None = extension

    def getName(self) -> str:
        return self.name if self.name else ""

    def getExtension(self) -> str:
        return self.extension if self.extension else ""

    def getFullName(self, force_lowercase_extension: bool = False) -> str:
        extension = f".{self.getExtension()}" if self.getExtension() else ""
        extension = extension.lower() if force_lowercase_extension else extension
        return self.getName() + (extension)


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


def getFullNameFromAbspath(
    abspath: str, lowercase_extension: bool = False
) -> str | None:
    if not os.path.exists(abspath):
        return None

    if os.path.isdir(abspath):
        return os.path.basename(abspath)

    split_name = os.path.basename(abspath).rsplit(".")
    name = split_name[0] if len(split_name) == 1 else ".".join(split_name[0:-1])
    extension = None if len(split_name) == 1 else split_name[-1]

    name = name if name else ""
    extension = f".{extension}" if extension else ""
    return name + (extension.lower() if lowercase_extension else extension)


def isFileOfFileTypes_fromAbspath(abspath: str, file_types: list[str]) -> bool | None:
    if not os.path.exists(abspath):
        return None

    if not os.path.isfile(abspath):
        return None

    split_name = os.path.basename(abspath).rsplit(".")
    if len(split_name) == 1:
        return False

    return split_name[-1].lower() in file_types


def isDirValid(abspath: str) -> bool:
    pathExists: bool = os.path.exists(abspath)
    isDir: bool = os.path.isdir(abspath)

    if not pathExists:
        print(f"Path does not exist: {abspath}\n")
        return False

    if not isDir:
        print(f"Path is not a directory: {abspath}\n")
        return False

    return True


def getPartsOfNameFromAbsPath(abspath: str) -> FileName | None:
    if not os.path.exists(abspath):
        print("Error: Not a valid path")
        return None

    if not os.path.isfile(abspath):
        print("Error: Not a file name")
        return None

    split_name = os.path.basename(abspath).rsplit(".")
    name = (
        None
        if split_name[0] == ""
        else split_name[0]
        if len(split_name) == 1
        else ".".join(split_name[0:-1])
    )
    extension = None if len(split_name) == 1 else split_name[-1]

    return FileName(name, extension)


def deleteFileFromAbsPath(
    abspath: str, on_failure: Callable[[str], None], max_retries: int = 5
) -> bool:
    if not os.path.exists(abspath) or not os.path.isfile(abspath):
        on_failure(f"Error: Invalid file: {abspath}")
        return False

    for attempt in range(max_retries):
        try:
            gc.collect()
            os.chmod(abspath, stat.S_IWRITE)
            os.remove(abspath)
            return True
        except OSError as e:
            if attempt < max_retries - 1:
                time.sleep(0.25)
            else:
                on_failure(f"Error deleting {abspath}: {e}")
                return False
    return False
