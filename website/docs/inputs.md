---
title: Inputs
icon: material/image-area
tags:
- Documentation
- Image
- Depth
---

For using custom images or depthmaps, provide them to the `input` command or method:

=== ":octicons-code-16: Python"

    ```python
    from depthflow.scene import DepthScene

    scene = DepthScene()
    scene.input(image=..., depth=...)
    ```

=== ":octicons-terminal-16: Command"

    ```bash
    # Also accepts URLs
    $ depthflow input --image base.png (...)
    ```

<small><b>Accepts:</b> <code>None | Path | Image | np.ndarray | str | BytesIO | bytes</code> • <b>Defaults:</b> None</small>

## Image

Main visual content in the scene. For better results, keep in mind and try to:

- Use images with a clear central object, and smooth or far-away backgrounds.
- Wires, fences, posts, hair threads, and small details _will_ cause artifacts.
- Use upscalers or denoisers to improve digital art sharpness.

Also, the scene's width and height will match the input for your convenience.

!!! info "You should handle downloads caching with packages like [requests-cache](https://pypi.org/project/requests-cache/) or [pooch](https://pypi.org/project/pooch/)."

## Depth

!!! success "When no depthmap is provided, an estimator is used on the input [#image](#image)."
    For selecting a model, refer to the [:material-magnify-scan: Estimators](./estimators.md) documentation.

A depthmap is a grayscale image where each pixel's intensity represents the distance between the camera and the scene at that point, also known as z-buffer in games/graphics. [#wikipedia](https://en.wikipedia.org/wiki/Depth_map)

<div>
    <img src="https://huggingface.co/datasets/huggingfacejs/tasks/resolve/main/depth-estimation/depth-estimation-input.jpg"
        width="49%" style="display:inline-block; vertical-align:top;">
    <img src="https://huggingface.co/datasets/huggingfacejs/tasks/resolve/main/depth-estimation/depth-estimation-output.png"
        width="49%" style="display:inline-block; vertical-align:top;">
</div>

!!! info "Matching aspect ratios isn't required, coordinates are absolute."

### Formats

There are two main formats for depthmaps:

- **Near is white**: Seen on the image above, and what the depthflow math expects.
- **Near is dark**: Inverse of the above, where near points are darker.

### Units

And also three main types of values:

- **Metric**: Values represent real-world distances, in meters, feet, etc.
- **Relative**: Values can only be compared against each other reliably.
- **Normalized**: Values are in a 0-1 range, loses proportions.

DepthFlow uses _normalized_, _near is white_ values in its [:octicons-device-camera-video-16: Camera](./camera.md) parameters.

