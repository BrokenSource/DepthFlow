---
title: Exporting
icon: octicons/video-16
tags:
- Documentation
---

DepthFlow supports realtime previews or video exporting.

!!! info "Ensure you have [FFmpeg](https://ffmpeg.org/) installed and available in PATH for video encoding"
    - For licensing and size reasons, it cannot be _easily_ distributed, and isn't a hard requirement.
    - Get from your package manager, or put executables in your working directory.

## Simple

Simply send an `output="video.mp4"` argument to the `scene.main` method/command:

=== ":octicons-code-16: Python"

    ```python
    scene = MyScene(backend="headless")
    scene.main(output="video.mp4")
    ```

=== ":octicons-terminal-16: Command"

    ```bash
    depthflow main --output video.mp4
    ```

:white_check_mark: **Note**: See all available options with `depthflow main --help`, most you already expect:

```python
scene.main(
    output="video.mkv",
    fps=60,
    time=10,
    width=1920,
    height=1080,
    ssaa=1.0,
)
```

## Codec

Very large topic, until ShaderFlow documentation is written, you can:

=== ":octicons-code-16: Python"
    Use your IDE linter to explore the `shaderflow.ffmpeg` module!

    ```python
    scene = MyScene()
    scene.ffmpeg.h264(preset="slow", crf=23)
    scene.ffmpeg.h264_nvenc(...)
    scene.ffmpeg.h265(...)
    scene.main(output="video.mp4")
    ```

=== ":octicons-terminal-16: Command"

    ```bash
    # See all available codecs
    depthflow --help

    # See a codec options with
    depthflow h264 --help

    # Use a codec with settings
    depthflow h264 --preset slow --crf 23 main -o video.mp4 (...)
    ```

<!-- -> See more in [ShaderFlow/Codecs](https://shaders.tremeschin.com/docs/codecs) documentation. -->

## Quality

The main things that affect the final video quality are:

1. **Depthmap precision**: DepthFlow is highly sensitive to _good relative depths_ between any two scene points, and **not** _object sillhouette precision_. Learn more at [:material-magnify-scan: Estimators](./estimators.md).
1. **SSAA Value**: Render at a higher resolution and downscales to output, default being 1.0 (pure). Must only go as high[^opengl-limits] as `2 * subsample` (default 2), the downscale kernel size, hurts quality otherwise. A value of 2.0 is plenty for final exports.
1. **Video resolution**: No gains in videos larger than input sources, _should_ at least match it. When using SSAA, zooming, or with large [#heights](./camera.md#height) or [#offsets](./camera.md#offset), a higher resolution 
1. **Quality parameter**: Explained in [:octicons-device-camera-video-16: Camera/#quality](./camera.md#quality).
1. **Image contents**: Explained in [:material-image-area: Inputs/#image](./inputs.md#image)
1. **Encoder settings**: Explained in [#codec](#codec).

[^opengl-limits]: OpenGL driver implementations have a maximum texture size, commonly 16384 or 32768 pixels depending on your GPU. Values above 2.0 may cause crashes for 4k or 8k output videos.

!!! warning "Some settings are O(N²) - know your hardware limits!"
    - Doubling the resolution is ~4x RAM, CPU usage.
    - Doubling SSAA is exactly 4x GPU usage.
