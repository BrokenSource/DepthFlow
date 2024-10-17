---
title: DepthFlow/Examples
---

<b><span class="the">T</span>his page</b> focus on getting started with DepthFlow, demonstrating basic usage, commands, and features. The main goal is to help you create your first 2.5D parallax effect videos quickly and easily, from the command line, web interface, or custom scripts.

<hr>

From any installation method, you can simply run `depthflow` or double click the executables to see all top-most available commands (entry points). You should see something like:

<div align="center">
    <img class="screenshot" src="https://github.com/user-attachments/assets/2785bd7c-97b1-45c7-b890-4ed48a556dfd">
</div>

!!! note "**Important**: The usage differs slightly between executable releases and others"
    When double clicking binaries, you've already implicitly ran this first `depthflow` entry point, in fact, this is equivalent to running `.\depthflow-windows-latest.exe` on a terminal. Any further commands inside the **interactive prompt** doesn't need it. For example, `depthflow gradio --share` becomes `gradio --share`!

You can run any of the commands above plus `#!ps --help` to list all options for that command.

For example, `depthflow gradio --help` will show all options for the web interface, running `depthflow --help` will show all CLI options (as is the default command).


## 🔘 Web interface

✅ On any installation method, you can run `depthflow gradio` to start the web interface. This will open a new tab in your default browser on a local server hosted in your machine:

<div align="center">
    <img src="https://github.com/user-attachments/assets/05b81504-d736-4c95-8e6f-9b4901c9eebd">
</div>

The user interface _should_ be somewhat self-explanatory, and is subject to change.

- 📁 **Input any** image on the top left, optionally upscale it; configure rendering options below and/or change the animations, and hit _"Render"_ to generate a video!

- ♻️ **You can pass** a `depthflow gradio --share` flag to have a temporary _public link_ of your instance, _proxied_ through [**Gradio**](https://www.gradio.app/)'s servers. Do this when hosting for a friend, or if you don't have access to the local network of a remote/rented server!

- ✏️ **Options that** could cause confusion include <kbd>Fit width</kbd> or <kbd>Fit height</kbd>. If you click _fit width_, the _height_ will be calculated to match the image's aspect ratio, e.g.

- 🚧 **Animations** system _will_ change and be improved. For now, enable presets and change their settings on the expandable accordion on the middle of the interface.

{% include-markdown "include/love-short.md" %}


<br>

## 🔘 Command line

✅ As **DepthFlow** is a [**ShaderFlow**](site:shaderflow) _"spin-off"_ - a custom Scene - most of its documentation on commands, behavior, issues and options are shared between the two.

- The examples of each section shows a single functionality, but you can combine them[^combine].

[^combine]: For example, when exporting a video, you can also input your image on the command chain.


<hr>

### Simplest command

Start a realtime window with the default image and animation with:

!!! example ""

    ```shell title=""
    depthflow main
    ```

- Walk around with <kbd>W A S D</kbd> or <kbd>Left click + Drag</kbd>
- Drag and drop image files or URLs to load them
- Press <kbd>Tab</kbd> for a dev menu with some options


<hr>

### Using your images

Load an input image, and start the main event loop with:

!!! example ""

    ```shell title=""
    # Local images, either relative or absolute paths
    depthflow input -i ./image.png main
    ```

    ```shell title=""
    # Remote images, like URLs
    depthflow input -i https://w.wallhaven.cc/full/2y/wallhaven-2y6wwg.jpg main
    ```

- **Note**: Make sure the image path exists, relative paths (not starting with `C:\` or `/`) are relative to where the the executable or current working directory of the shell or is.


<hr>

### Exporting a video

Render 10 seconds of the animation to a video file with default settings with:

!!! example ""

    ```shell title=""
    depthflow main -o ./output.mp4
    ```

!!! tip "See all rendering options with `depthflow main --help`"

#### Resolution

The output resolution, by default, will match the input image's one. You can send either `-w` or `-h` to force one component and fit the other based on the image's aspect ratio:

!!! example ""

    ```shell title=""
    # Renders a 2560x1440 (Quad HD) video
    depthflow input -i ./image16x9.png main -h 1440
    ```

    ```shell title=""
    # Width is prioritized, this renders a 500x500 video
    depthflow input -i ./image1000x1000.png main -w 500 -h 800
    ```

#### Looping

The output video will scale and loop perfectly, with a period set by the `--time` parameter:

!!! example ""

    ```shell title=""
    # Loops every 5 seconds
    depthflow main -o ./output.mp4 --time 5
    ```

    ```shell title=""
    # 12 second video with 3 loops happening
    depthflow main -o ./output.mp4 --time 4 --loops 3
    ```

#### Video encoder

You can also easily change the video encoder:

!!! example ""

    You can see all available codecs in `depthflow --help` !

    ```shell title=""
    # Configure the H264 codec, see also `depthflow h264 --help`
    depthflow h264 --preset fast main -o ./output.mp4
    ```

    ```shell title=""
    # Use the H264 codec with NVENC on a NVIDIA GPU
    depthflow h264-nvenc main -o ./output.mp4
    ```


    ```shell title=""
    # I don't even have a RTX 40 to test this lol
    depthflow av1-nvenc main -o ./output.mp4
    ```

#### Quality

The video is eternal, so getting the best render quality even if it takes longer is important. There's a couple of main factors that defines the final video quality:

1. **Resolution**: A combination of the input image and the exported video's resolution. Rendering at a higher resolution than the input image will not improve quality.

2. [**Super Sampling Anti Aliasing**](https://en.wikipedia.org/wiki/Supersampling): Rendering at a higher internal resolution and then downscaling to the output target mitigates edge artifacts and smooths them. The default is 1.2, and the maximum quality gains happen at 2.0, don't go above it.

3. **Quality parameter**: The `depthflow main --quality 50` parameter defines how accurate calculating the projection's intersections are. A value of 0 is sufficient for subtle movements, and will create 'layers' artifacts at higher values. The default is 50, which is actually overkill for most cases, given how much optimized the code is.

4. **Depth map**: Defines the accuracy of the parallax effect. The default estimator is a state of the art balance of speed, portability, quality, and should be enough.

5. **Video codec**: The encoder compresses the video from unimaginably impractical sizes of raw data to something manageable. Briefly, CPU encoders yields the best compression, file sizes, and quality, but are slow(er) than GPU encoders, which are _"worse"_ in every other situation. There's no better quality than the realtime window itself.

!!! example ""

    ```shell title=""
    # The stuff explained above in a command:
    depthflow main --quality 80 --ssaa 2 -o ./output.mp4
    ```

<hr>

### Using an upscaler

Upscale the input image before rendering the video with:

!!! example ""

    ```shell title=""
    # Use RealESRGAN to upscale the image (https://github.com/xinntao/Real-ESRGAN)
    depthflow realesr input -i ./image.png main -o ./output.mp4
    ```

    ```shell title=""
    # Use Waifu2x to upscale the image (https://github.com/nihui/waifu2x-ncnn-vulkan)
    depthflow waifu2x input -i ./image.png main -o ./output.mp4
    ```

<hr>

### Custom animations

!!! warning "🚧 Animations are work in progress, and will change substantially 🚧"

You can use a couple of high quality presets with:

!!! example ""

    See any of `depthflow 'preset' --help` for more options!

    ```shell title=""
    # Add a horizontal motion to the camera
    depthflow horizontal main
    ```

    ```shell title=""
    # Add a vertical motion to the camera
    depthflow vertical --linear main
    ```

    ```shell title=""
    # Add a circular motion to the camera
    depthflow circle --intensity 0.3 main
    ```

    ```shell title=""
    # Add a dolly zoom to the camera
    depthflow dolly --reverse -i 2 main
    ```

    ```shell title=""
    # Add a zoom-in motion to the camera
    depthflow zoom main
    ```

{% include-markdown "include/love-short.md" %}


<br>

## 🔘 Scripts

Talk is cheap, and if you're here, you know what you want 😅

- All scripts below are self-explanatory: <sup>hopefully</sup>

### Simplest

!!! example "This simplest script is the same as running the main entry point directly"
    ```python
    {% include-markdown "../../depthflow/examples/basic.py" %}
    ```

### Custom

!!! example "You can create custom animations, and manage/automate everything within Python"
    ```python
    {% include-markdown "../../depthflow/examples/custom.py" %}
    ```

### Complex

!!! example "This monstruous script combines batch and parallel processing, animation variations"
    ```python
    {% include-markdown "../../depthflow/examples/complex.py" %}
    ```

{% include-markdown "include/love-short.md" %}


<br>

## 🎓 Next Steps

- Explore the [Parameters](site:depthflow/parameters) documentation to understand how to fine-tune your animations.
- Check out the [ShaderFlow](site:shaderflow) documentation for more rendering and exporting options.
- Dive into the [Foundations](site:depthflow/learn/foundations) page to understand the math behind DepthFlow.

Happy animating with DepthFlow! 🌊✨
