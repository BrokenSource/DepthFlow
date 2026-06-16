---
title: Estimators
icon: material/magnify-scan
tags:
- Documentation
- Estimators
- Depth Anything
---

DepthFlow provides wrappers for SOTA [Monocular Depth Estimation](https://huggingface.co/docs/transformers/tasks/monocular_depth_estimation) models with features like:

- **Cached** results on disk to reduce import times and computational costs across runs.
- **Mitigate** projection artifacts by fattening the edges, less foreground blending.

## Usage

For using a specific [#model](#models), look for the [`depthflow.estimators`](https://github.com/BrokenSource/DepthFlow/tree/main/depthflow/estimators) package or command line help:

### DepthScene

=== ":octicons-code-16: Python"

    ```python
    # Already initialized as default
    from depthflow.estimators.anything import DepthAnythingV2
    from depthflow.scene import DepthScene

    scene = DepthScene()
    scene.estimator = DepthAnythingV2(model="small")
    ```

=== ":octicons-terminal-16: Command"

    ```bash
    # See available commands
    $ depthflow --help

    # See estimator options
    $ depthflow da2 --help

    # Use DepthAnythingV2 small model
    $ depthflow da2 --model small (...)
    ```

### Standalone

Wrappers can also be used outside the scene, but always use and returns `np.ndarray`:

```python
from depthflow.estimators.anything import DepthAnythingV2

estimator = DepthAnythingV2()
depthmap = estimator.estimate(image=...)
```

## Models

-> Options below are roughly ordered by a combination of quality, size, and speed.

<!----------------------------------------------------------------------------->

### [Depth Anything v2](https://github.com/DepthAnything/Depth-Anything-V2)

!!! success "Recommended and the default model"

!!! quote "Showcase"
    <img src="https://raw.githubusercontent.com/DepthAnything/Depth-Anything-V2/main/assets/teaser.png" width="100%"/>

<small><b>Warning</b>: Models other than Small are under CC BY-NC 4.0 (non-commercial + attribution) licenses.</small>

<!----------------------------------------------------------------------------->

<hr>

### [Depth Anything v3](https://github.com/ByteDance-Seed/depth-anything-3)

!!! info "Currently awaiting a [transformers](https://github.com/huggingface/transformers) safetensors release or alternatives"
    - Likely available through the non-existing the [`*-hf`](https://huggingface.co/depth-anything/DA3-SMALL-hf) version of [depth-anything/DA3-SMALL](https://huggingface.co/depth-anything/DA3-SMALL)
    - The [pypi release](https://pypi.org/project/depth-anything-3/) contains **way too many** problematic and limiting [dependencies](https://github.com/ByteDance-Seed/Depth-Anything-3/blob/41736238f5bced4debf3f2a12375d2466874866d/pyproject.toml#L14-L42), eg:
        - `open3d`: Not used in Monocular Depth Estimation (MDE), has no Python 3.13+ prebuilt wheels.
        - `numpy<2`: Version 1.26.4 was release in Feb 2025, the ecosystem already moved forward.
    - Fork at [BrokenSource/Depth-Anything-3](https://github.com/BrokenSource/Depth-Anything-3) reducing it, but I don't want to maintain a pypi package.
    - May add a runtime git+ install option, but that is frowned upon.

!!! quote "Showcase"
    <img src="https://depth-anything-3.github.io/assets/teaser.png" width="100%"/>

<!----------------------------------------------------------------------------->

<hr>

### [Depth Anything v1](https://github.com/LiheYoung/Depth-Anything)

!!! quote "Showcase"
    <img src="https://raw.githubusercontent.com/LiheYoung/Depth-Anything/main/assets/teaser.png" width="100%"/>

<small><b>Warning</b>: Models other than Small are under CC BY-NC 4.0 (non-commercial + attribution) licenses.</small>

<!----------------------------------------------------------------------------->

<hr>

### [DepthPro](https://github.com/apple/ml-depth-pro)

!!! warning "Not implemented"
    - Long setup times on class initialization, large Apple CDN download.
    - Unless I misused, perceptual results are worse than [DAv2](#depth-anything-v2).

!!! quote "Showcase"
    <img src="https://raw.githubusercontent.com/apple/ml-depth-pro/main/data/depth-pro-teaser.jpg" width="100%"/>

<!----------------------------------------------------------------------------->

<hr>

### [Marigold](https://github.com/prs-eth/Marigold)

!!! warning "Not implemented"
    - Large system requirements on disk, memory and computation.
    - Unless I misused, perceptual results are worse than [DAv1](#depth-anything-v1).

!!! quote "Showcase"
    <img src="https://raw.githubusercontent.com/prs-eth/Marigold/main/doc/teaser_marigold_depth.png" width="100%"/>

<!----------------------------------------------------------------------------->

<hr>

### [ZoeDepth](https://github.com/isl-org/ZoeDepth)

!!! failure "No longer maintained, early historical model, vastly superseded."
