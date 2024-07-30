# 🌊 DepthFlow

!!! warning "🚧 Better Documentation is Work in Progress 🚧"

{% include-markdown "include/install.md" %}

## Running DepthFlow
With PyTorch installed, simply run `depthflow`, a window will open

- Models will be Downloaded on the first run

### Rendering Options
- Run `depthflow --help` for all Options and Exporting to a Video File

### Selecting the input image
- Run `depthflow input --help`. The exported Video File Image is the one defined here
- Drag and drop an Image File or URL From your Browser to the Window in Realtime Mode

**Note**: This resizes<sup>*1</sup> the Window to the image resolution, there's options:

- Only sending `--width` or `--height` adjusts the other to Aspect Ratio
- Sending Both will force the resolution (can also be set on `main -w -h`)
- Sending None will use the Image's resolution (default)
- Use `--scale` to post-multiply the new resolution

<sup><i>*1 The Resolution is limited by the `MONITOR=0` Flag (0=Primary), only on Realtime mode</i></sup>

### Animation Presets
There's currently no mechanism for presets, but it is planned

- For now, manually change the `.update()` function on `DepthFlow/DepthFlow.py`

### Full Examples
- `depthflow main (--render | -r)`
- `depthflow main -r -f 30`
- `depthflow main -r -o ./video_name --format mkv`
- `depthflow input --image (url | path) main --render -s 2`
- `depthflow main -r -t 2 --open`
- `depthflow input -i (image) -d (depth) main`
- `depthflow input -i (image) -w 600 --scale 2 main -r`

<b>Note</b>: A high SSAA `-s 1.5` is recommended for antialiasing due the Steep Parallax
