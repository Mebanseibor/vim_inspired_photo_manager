# VIM inspired Photo Manager

"Inspired by [VIM](https://github.com/vim/vim) keybindings, a software that manages photos"

## Features

- Displaying the images

- Utilizing [VIM keybindings](./docs/keybindings.md)

- Optimized:
  - Utilizes caching:
    - Utilize caching saves processing time on subsequent processing of the same
      image
    - File relocation independent cache utilization

## Instructions

### Using your base system

#### Requirements

##### Python

> [!TIP]
>
> - Commands to install Python in Linux:
>   - `apt update && apt install -y python3 pip`
> - You can install the packages by excuting the following command on the "requirements.txt" file:
>   - `pip install -r requirements.txt`

- Version: `3.12`
- Python packages:
  - numpy
  - pillow
  - customtkinter
  - xxhash

#### Steps

- Clone or download this repository:
- Run the software:
  - Run the bash script [`start.sh`](./start.sh) or run the command `python -m core_modules.main`

### Using dockers containers

> [!NOTE]
> Only the CLI version is usable

- Build an image using [`dockerfile`](./dockerfile)

---

## Future planned features

- CLI:
  - Working only from the terminal (Limited features)

- Displaying RAW files
