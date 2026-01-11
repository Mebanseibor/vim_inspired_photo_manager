# VIM inspired Photo Manager

"Inspired by [VIM](https://github.com/vim/vim) keybindings, a software that manages photos"

## Features

- Displaying images

- Visually see the intended action for the image:
  - Actions:
    - Keep
    - Delete
    - Mark for review

- Utilizing [VIM keybindings](./docs/keybindings.md)

### Other features

- Utilizes caching:
  - Saves processing time on subsequent processing of the same image
  - Cache utilization is independent of file relocation

## Instructions

### Requirements

#### Python

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

### Steps

- Clone or download this repository:
- Run the software:
  - Run the bash script [`start.sh`](./start.sh) or run the command `python -m core_modules.main`

---

## Planned future features

- Deleting intended images
- Displaying RAW files
