import os
import xxhash

from ..shared import shared as s

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]


class FileSystemItem:
    def __init__(self, abspath: str):
        self.abspath: str = abspath
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
        print(f"abs_path:\t{self.abspath}")

    def fullName(self):
        name = self.name if self.name else ""
        ext = f".{self.extension}" if self.extension else ""
        return name + ext

    def is_image(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        return self.extension in IMAGE_EXTENSIONS


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


def list_of_fs_items_at(
    abspath_dir: str, images_only: bool = False, max_items: int | None = None
) -> s.Result:
    if not os.path.exists(abspath_dir):
        return s.Result(None, False, f"Path '{abspath_dir}' does not exist")

    if not os.path.isdir(abspath_dir):
        return s.Result(None, False, f"Path '{abspath_dir}' was not a directory")

    # creating a fs_item
    file_paths = os.listdir(abspath_dir)
    files = []
    counter_file_paths = 0
    counter_selected_items = 0
    for file_path in file_paths:
        joined_path = os.path.join(abspath_dir, file_path)
        abspath_file = os.path.abspath(joined_path)
        fs_item = FileSystemItem(abspath_file)
        counter_file_paths += 1
        progress = counter_file_paths / len(file_paths) * 100
        print(f"Checked file system item ({progress:06.2f}%): {fs_item.fullName()}")
        if images_only:
            if fs_item.is_image():
                files.append(fs_item)
            else:
                continue
        else:
            files.append(fs_item)

        counter_selected_items += 1
        if max_items:
            if counter_selected_items >= max_items:
                break

    print(f"Number of fs items available:\t{len(file_paths)}")
    print(f"Number of fs items selected:\t{counter_selected_items}")

    return s.Result(files)


def promptPath(
    prompt_till_valid: bool = False, quit_command: str | None = None
) -> str | None:
    quit_command_message = f" (To quit, enter {quit_command})" if quit_command else ""
    while True:
        print(f"Enter path{quit_command_message}:")
        path = input().strip()

        if quit_command and path == quit_command:
            return None

        if not prompt_till_valid:
            return path

        abspath = os.path.abspath(path)
        pathExists: bool = os.path.exists(abspath)
        isDir: bool = os.path.isdir(abspath)

        if pathExists and isDir:
            return abspath

        if not pathExists:
            print(f"Path does not exist: {abspath}\n")
            continue

        if not isDir:
            print(f"Path is not a directory: {abspath}\n")
            continue


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


def getFilePathsAtAbspath(
    abspath_dir: str, images_only: bool = False, max_items: int | None = None
) -> list[str] | None:
    if not os.path.exists(abspath_dir) or not os.path.isdir(abspath_dir):
        return None

    file_paths = os.listdir(abspath_dir)

    abspath_files = []
    for file_path in file_paths:
        abspath_files.append(os.path.abspath(os.path.join(abspath_dir, file_path)))

    if not images_only:
        return abspath_files

    abspath_files_images_only = []

    for file_path in abspath_files:
        abspath_file = os.path.abspath(os.path.join(abspath_dir, file_path))
        if isImageFromAbspath(abspath_file):
            abspath_files_images_only.append(abspath_file)

    return abspath_files_images_only


def isImageFromAbspath(abspath: str) -> bool | None:
    if not os.path.exists(abspath):
        return None

    if not os.path.isfile(abspath):
        return None

    split_name = os.path.basename(abspath).rsplit(".")
    if len(split_name) == 1:
        return False

    return split_name[-1].lower() in IMAGE_EXTENSIONS
