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
  <img src="https://github.com/BrokenSource/DepthFlow/assets/29046864/7f73775e-0b08-4a4f-bf97-7cb8f3aecad8" alt="Depth Map">
  <br>
  The Depth Map was estimated with <a href="https://github.com/isl-org/ZoeDepth"><b>ZoeDepth</b></a> 🚀
  <br>
  <br>
</details>

<br>
<br>

# 📦 Installation

## 🪛 From Source Code

> 🔴🟡🟢
>
> **Download** our [**Monorepo**](https://github.com/BrokenSource/BrokenSource#-running-from-the-source-code) with all the code and Projects first
>
> <sub><b>Note:</b> You cannot run this project in development mode without it !</sub>

- **DepthFlow** directly uses [**ShaderFlow**](https://github.com/BrokenSource/ShaderFlow). _Check it out!_ 🚀

<br>

After running the `brakeit` script on the [**Monorepo**](https://github.com/BrokenSource/BrokenSource#-running-from-the-source-code) and inside the Virtual Environment,

- Run the command: `broken depthflow`

A real time window should pop up.

#### Selecting the input image
- Run `broken depthflow parallax --help` for parallax options

- You can also drag and drop an Image File or URL From your Browser

#### Rendering Options
- Run `broken depthflow --help` for options and rendering

#### Full Examples
- `broken depthflow (--render | -r)`
- `broken depthflow -r -w 1280 -h 720 -f 30`
- `broken depthflow -r -o ./video_name --format mkv`
- `broken depthflow parallax --image (url | path) main --render -s 2`
- `broken depthflow -r -t 2 --open`
- `broken depthflow parallax -i (image) -d (depth) main`

<b>Note</b>: A high SSAA `-s 1.5` is recommended for antialiasing due the Steep Parallax

<br>

## 🔮 Prebuilt Binaries
Whenever stuff gets more stable, we'll likely release PyPI packages so you can just `pip install shaderflow` and run it directly from the source code or prebuilt binaries that you can just download and run `./shaderflow scene.py`

<br>
<br>

# 🚀 Using your GPU

> By default, Pytorch will be installed with CPU support

For Faster **Depth Estimation**, you can switch the PyTorch backend:

<br>

**NVIDIA** + CUDA:
- Have the [NVIDIA Drivers](https://www.nvidia.com/download/index.aspx) installed
- Run the command: `broken depthflow poe cuda`

<br>

**AMD** + ROCm:
- Run the command: `broken depthflow poe rocm`

<br>

**macOS**:
- Run the command: `broken depthflow poe mac`

<br>

**CPU**:
- Run the command: `broken depthflow poe cpu`

<br>

**Reverting** to the default:
- Run the command: `broken depthflow poe default`

<br>
<br>

# ⚖️ License

**See [BrokenSource](https://github.com/BrokenSource/BrokenSource) Repository** for the License of the Code, Assets, Projects and User Generated Content.

</div>