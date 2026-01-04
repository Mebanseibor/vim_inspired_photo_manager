# README

"A passion project software that assist me in my photo management workflow as a
photographer"

## Features

- Displaying the images

- Utilizing [VIM keybindings](./docs/keybindings.md)

- Optimized:
  - Utilizes caching:
    - Utilize caching saves around _78%_-_93%_ of the processing time
    - File relocation independent cache utilization

## Instructions

### Using dockers containers

- Build an image using [`dockerfile`](./dockerfile)
- Only the CLI version is usable

### Using your base system

#### Requirements

- Python version `3.12`
- Python packages:
  - Individual packages:
    - numpy
    - pillow
    - customtkinter
    - xxhash
  - Install the pacakges by excuting the following command on the "requirements.txt" file:
    - `pip install -r requirements.txt`

#### Steps

- Clone or download this repository:
- Run the software:
  - Run the bash script [`start.sh`](./start.sh) or run the command `python -m core_modules.main`

---

## Future planned features

- CLI:
  - Working only from the terminal (Limited features)

- Displaying RAW files

- Performance improvements:
  - Reducing RAM usage
  - Implementing sliding-window caching
