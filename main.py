import os

import core_modules.cache_manager as cM
import core_modules.gui_manager as guiM

if __name__ == "__main__":
    print("\n\n----- Start of the program -----\n\n")

    def makeFolders():
        abspath_cache_folder = os.path.abspath(cM.CACHE_FOLDER)

        if not os.path.exists(abspath_cache_folder):
            print(f"Creating non-existant cache folder at: {cM.CACHE_FOLDER}")
            os.makedirs(abspath_cache_folder)

    makeFolders()

    guiM.gui()

    print("\n\n----- End of the program -----")
