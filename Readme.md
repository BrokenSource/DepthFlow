【☰】Table of Contents 👆

<div align="justify">

<div align="center">
  <img src="./DepthFlow/Resources/Images/DepthFlow.png" width="200">

  <h1>DepthFlow</h1>

  <img src="https://img.shields.io/github/stars/BrokenSource/DepthFlow?style=flat" alt="Stars Badge"/>
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhits.dwyl.com%2FBrokenSource%2FDepthFlow.json%3Fshow%3Dunique&label=Visitors&color=blue"/>
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhits.dwyl.com%2FBrokenSource%2FDepthFlow.json&label=Page%20Views&color=blue"/>
  <img src="https://img.shields.io/github/license/BrokenSource/DepthFlow?color=blue" alt="License Badge"/>
  <a href="https://t.me/brokensource">
    <img src="https://img.shields.io/badge/Telegram-Channel-blue?logo=telegram" alt="Telegram Channel Badge"/>
  </a>
  <a href="https://discord.gg/KjqvcYwRHm">
    <img src="https://img.shields.io/discord/1184696441298485370?label=Discord&color=blue" alt="Discord Badge"/>
  </a>

  <sub> 👆 Out of the many **Explorers**, you can be among the **Shining** stars who support us! ⭐️ </sub>

  <br>

  **[**[**DepthFlow**](https://github.com/BrokenSource/DepthFlow)**]**: Image to → **2.5D Parallax** Effect Video. A Professional **[**[**Depthy**](https://depthy.stamina.pl)**]** Alternative.
</div>

<br>

👇 Right click and **loop me**!

https://github.com/BrokenSource/DepthFlow/assets/29046864/cf9e23f0-e64b-435a-8762-e49936602071

<sup><b>Note:</b> Yes, the only input to DepthFlow was the Original Image</sup>

<br>

<details>
<summary>🎩 <b>Click</b> to see the Original Image </summary>
  <br>
  <a href="https://wallhaven.cc/w/pkz5r9">
    <img src="https://github.com/BrokenSource/DepthFlow/assets/29046864/1975fdc9-9517-4700-88dd-ed8175ab813f" alt="Original Image">
  </a>
  <br>
  <b>Source:</b> <a href="https://wallhaven.cc/w/pkz5r9">Wallhaven</a>. All images remain property of their original owners. ⚖️
  <br>
  <br>
</details>

<details>
<summary>🪄 <b>Click</b> to see the Estimated Depth map </summary>
  <br>
  <img src="https://github.com/BrokenSource/DepthFlow/assets/29046864/bace7072-5437-4ffd-96f2-91b9be3a4fed" alt="Depth Map">
  <br>
  The Depth Map was estimated with <a href="https://github.com/LiheYoung/Depth-Anything"><b>DepthAnything</b></a> 🚀
  <br>
  <br>
</details>

<br>
<br>

# 📦 Installation

- **DepthFlow** directly uses [**ShaderFlow**](https://github.com/BrokenSource/ShaderFlow). _Check it out!_ 🚀
- Amazing Depth Estimations by [**DepthAnything**](https://github.com/LiheYoung/Depth-Anything)

<br>

> 🔴🟡🟢&nbsp; **For Extra** and **Alternative Installation Help**, check out the [**Monorepo**](https://github.com/BrokenSource/BrokenSource#-running-from-the-source-code)
>
> - **💠 Windows**: Open a Folder, Press <kbd>Ctrl+L</kbd>, Run `powershell` and execute
>   ```ps
>   irm https://brakeit.github.io/get.ps1 | iex
>   ```
>
> - **🐧 Linux and MacOS 🍎**: Open a Terminal in some Directory and run
>   ```ps
>   /bin/bash -c "$(curl -sS https://brakeit.github.io/get.sh)"
>   ```
> <sub><b>⚠️ Warning:</b> Recent Tooling changes may cause new issues. Get in touch for any issues 🤝</sub>
>
> <sub><b>Note:</b> The commands above are safe. You can read what they do <b><a href="https://github.com/Brakeit/brakeit.github.io">here</a></b>.</sub>

<br>

After activating the Virtual Environment on `.venv`, install [**PyTorch**](https://pytorch.org/):

<br>

## 🚀 Chosing a PyTorch Flavor
**Pick** one option below for your **Hardware** and run the **Command**. Have **Drivers installed**

<div align="center">

  | Type    | **Hardware** | **Command** | **Notes** |
  |---------|--------------|-------------|-----------|
  | GPU     | [**NVIDIA**](https://www.nvidia.com/download/index.aspx) + [CUDA](https://en.wikipedia.org/wiki/CUDA) | `poe cuda` | -
  | GPU     | [**AMD**](https://www.amd.com/en/support) + [ROCm](https://en.wikipedia.org/wiki/ROCm) | `poe rocm` | [Linux only, >= RX 5000](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html)
  | GPU     | Intel ARC    |  -          | -   |
  | CPU     | Any          | `poe cpu`   | Slow |
  | MacOS   | -            | `poe base`  | -   |

</div>

<sub><b>Note:</b> I don't have an AMD GPU or Macbook to test and give full support</sub>

<br>

## 🎮 Running DepthFlow
With PyTorch installed, simply run `depthflow`, a window will open
- Models will be Downloaded on the first run

### Rendering Options
- Run `depthflow --help` for options and rendering

### Selecting the input image
- Run `depthflow input --help` for options on the CLI/Rendering
- Drag and drop an Image File or URL From your Browser

**Note**: This resizes the Window to the image size, there's options:
- Only sending `--width` or `--height` adjusts the other to Aspect Ratio
- Sending Both will force the resolution (can also be set on `main -w -h`)
- Sending None will use the Image's resolution (default)
- Use `--scale` to post-multiply the new resolution

### Animation Presets
There's currently no mechanism for presets, but it is planned
- For now, manually change the `.update()` function on `DepthFlow/DepthFlow.py`

### Full Examples
- `depthflow (--render | -r)`
- `depthflow -r -f 30`
- `depthflow -r -o ./video_name --format mkv`
- `depthflow input --image (url | path) main --render -s 2`
- `depthflow -r -t 2 --open`
- `depthflow input -i (image) -d (depth) main`
- `depthflow input -i (image) -w 600 --scale 2 main -r`

<b>Note</b>: A high SSAA `-s 1.5` is recommended for antialiasing due the Steep Parallax


<br>
<br>

# ⚖️ License

**See [BrokenSource](https://github.com/BrokenSource/BrokenSource) Repository** for the License of the Code, Assets, Projects and User Generated Content

- **DepthFlow** Shader is CC-BY-SA 4.0, just attribute on videos and same-license modifications :)

</div>