<div align="center">

# VIM-inspired Photo Manager

**Keyboard base photo management software**

_"Make decisions with less actions: keeping or deleting an image"_

[![Download](https://img.shields.io/badge/Download-Now-3d59a8?style=for-the-badge&logoColor=ffffff&labelColor=111111&colorA=3d59a8&colorB=3d59a8)](https://github.com/Mebanseibor/vim_inspired_photo_manager/releases/latest)

[![View keybindings](https://img.shields.io/badge/Keybindings-View-3d59a8?style=for-the-badge&logoColor=ffffff&labelColor=111111&colorA=3d59a8&colorB=3d59a8)](./docs/keybindings.md)

<br/>

_Inspired by_

<a href="https://github.com/vim/vim">
<img src="https://img.shields.io/badge/Vim-3d59a8?style=flat&logo=vim&logoColor=ffffff" width="56">
</a>

<br/>
<br/>

![Demo](./docs/assets/demo.gif)

</div>

---

## Features

- Support for jpegs and raws being located in different directories

- Visually see the intended action for the image:
  - Actions:
    - Keep
    - Delete

- Inspecting an image:
  - Panning
  - Zooming

### Other notable features

- Utilizes caching:
  - Saves processing time on subsequent processing of the same image
  - Cache utilization is independent of file relocation

---

## Instructions to build the software from source

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
  - Run the command `python main`
