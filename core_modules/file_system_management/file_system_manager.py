import os
import xxhash

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
RAW_EXTENSIONS = ["arw"]

IMAGES_ONLY_KEY = "images_only"
RAWS_ONLY_KEY = "raw_files_only"


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

    def is_raw(self) -> bool:
        if not self.is_file:
            return False

        if not self.extension:
            return False

        return self.extension in RAW_EXTENSIONS


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


def promptPath(
    text: str | None, prompt_till_valid: bool = False, quit_command: str | None = None
) -> str | None:
    quit_command_message = f" (To quit, enter {quit_command})" if quit_command else ""
    while True:
        prompt_text = text if text else f"Enter path{quit_command_message}:"
        print(prompt_text)
        path = input().strip()

        if quit_command and path == quit_command:
            return None

        if not prompt_till_valid:
            return path

        abspath = os.path.abspath(path)
        if isDirValid(abspath):
            return abspath


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


def getFilePathsAtAbspathForFormats(
    abspath_dir: str,
    file_formats: dict[str, bool],
) -> dict[str, list[str]] | None:
    if not os.path.exists(abspath_dir) or not os.path.isdir(abspath_dir):
        return None

    file_paths = os.listdir(abspath_dir)

    abspath_files = []
    for file_path in file_paths:
        abspath_files.append(os.path.abspath(os.path.join(abspath_dir, file_path)))

    result = {}

    abspath_files_raws_only = []
    abspath_files_images_only = []

    for file_path in abspath_files:
        abspath_file = os.path.abspath(os.path.join(abspath_dir, file_path))

        if file_formats.get(RAWS_ONLY_KEY) and isAbspathOfFileTypes(
            abspath_file, RAW_EXTENSIONS
        ):
            abspath_files_raws_only.append(abspath_file)
        if file_formats.get(IMAGES_ONLY_KEY) and isAbspathOfFileTypes(
            abspath_file, IMAGE_EXTENSIONS
        ):
            abspath_files_images_only.append(abspath_file)

    result[IMAGES_ONLY_KEY] = abspath_files_images_only
    result[RAWS_ONLY_KEY] = abspath_files_raws_only

    return result


def isAbspathOfFileTypes(abspath: str, file_types: list[str]) -> bool | None:
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
