---
title: Commands
icon: octicons/command-palette-16
---

✅ As **DepthFlow** is a [ShaderFlow](https://github.com/BrokenSource/ShaderFlow) _"spin-off"_ - a custom Scene - most of its documentation on commands, behavior, issues and options are shared between the two.

- The examples of each section shows a single functionality, but you can combine them.


### Simplest command

Start a realtime window with the default image and animation with:

!!! example ""

    ```shell title=""
    depthflow main
    ```

- Walk around with <kbd>W A S D</kbd> or <kbd>Left click + Drag</kbd>
- Drag and drop image files or URLs to load them
- Press <kbd>Tab</kbd> for a dev menu with some options


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


### Exporting a video

Render 5 seconds of the animation to a video file with default settings with:

!!! example ""

    ```shell title=""
    depthflow main -o ./output.mp4
    ```

!!! tip "See all rendering options with `depthflow main --help`"

#### Resolution

The output resolution will match the input image by default. You can pass either `--width/-w` or `--height/-h` to force one component and fit the other based on the image's aspect ratio:

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
    # 5 second video with 1 loop happening
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
    # Configure the H264 codec
    depthflow h264 --preset veryfast main -o ./output.mp4
    ```

    ```shell title=""
    # Use the H264 codec with NVENC on a NVIDIA GPU
    depthflow h264-nvenc main -o ./output.mp4
    ```

    ```shell title=""
    # Only supported in RTX 4000 and newer GPUs
    depthflow av1-nvenc main -o ./output.mp4
    ```

#### Quality

The video is eternal, so getting the best render quality even if it takes longer is important. There's a couple of main factors that defines the final video quality:

1. **Resolution**: A combination of the input image and the exported video's resolution. Rendering at a higher resolution than the input image will not improve quality.

2. [**Super Sampling Anti Aliasing**](https://en.wikipedia.org/wiki/Supersampling): Renders at a higher internal resolution and then downscaling to the output target mitigates edge artifacts and smooths them. The default is 1.2, good quality with 2, best with 4, don't go above it. Uses `N^2` times more GPU power.

3. **Quality parameter**: The `depthflow main --quality 50` parameter defines how accurate the projection's intersections are. A value of 0 is sufficient for subtle movements, and will create _"layers"_ artifacts at higher offsets. The default is 50, which is actually overkill for most cases.

4. **Depth map**: Defines the accuracy of the parallax effect. The default estimator is a state of the art balance of speed, portability, quality, and should be enough.

5. **Video codec**: The encoder compresses the video from unimaginably impractical sizes of raw data to something manageable. Briefly, CPU encoders yields the best compression, file sizes, and quality, but are slower than GPU encoders, which are _"worse"_ in every other aspect. Max quality is seen only on the realtime window, as it is the raw data itself.

!!! example ""

    ```shell title=""
    # The stuff explained above in a command:
    depthflow main --quality 80 --ssaa 2 -o ./output.mp4
    ```

    ```
    # Extremely slow, but the best quality
    depthflow main --quality 100 --ssaa 4 -o ./output.mp4
    ```


### Using an upscaler

Upscale the input image before rendering the video with:

!!! example ""

    ```shell title=""
    # Use Upscayl to upscale the image (https://github.com/upscayl/upscayl)
    depthflow upscayl -m digital-art input -i ./image.png main -o ./output.mp4
    ```

    ```shell title=""
    # Use Waifu2x to upscale the image (https://github.com/nihui/waifu2x-ncnn-vulkan)
    depthflow waifu2x input -i ./image.png main -o ./output.mp4
    ```


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


### Batch processing

Batch processing is better done externally with scripts:

<!-- Todo: Examples -->

--8<-- "include/love-short.md"
