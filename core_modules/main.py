import os

from .cache_management import cache_manager as cM
from .file_system_management import file_system_manager as fsM
from .gui import gui_manager as guiM
from .shared import shared as s


def cli():
    while True:
        print("\n\n")
        print(f"Current absolute path:\t{s.CURR_ABS_PATH}")
        path = fsM.promptPath(prompt_till_valid=True, quit_command=command_quit)

        if not path:
            break

        abspath = os.path.abspath(os.path.join(s.CURR_ABS_PATH, path))

        list = fsM.list_of_fs_items_at(abspath)

        if not list.is_successful:
            print(list.formatted_err_msg())
            exit()

        for item in list.result:
            item.display_details()
            print("\n")


if __name__ == "__main__":
    print("\n\n----- Start of the program -----\n\n")

    def makeFolders():
        abspath_cache_folder = os.path.abspath(cM.CACHE_FOLDER)

        if not os.path.exists(abspath_cache_folder):
            print("Creating non-existant cache folder")
            os.makedirs(abspath_cache_folder)

    makeFolders()

    command_quit = "q!"

    # choosing an interface
    i_gui = "1"
    i_cli = "2"
    while True:
        print("\n\n")
        print(f"To quit, enter: '{command_quit}'")
        print("Pick an interface:")
        print(f"{i_gui}. GUI (With window interface)")
        print(f"{i_cli}. CLI (In terminal)")

        choice = input()

        if choice == command_quit:
            break
        elif choice == i_gui:
            print("Opening GUI")
            guiM.gui()
        elif choice == i_cli:
            print("Opening CLI")
            cli()
        else:
            print("Invalid choice")
            continue
        break

    print("\n\n----- End of the program -----")
