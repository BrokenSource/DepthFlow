---
title: Changelog
icon: material/file-document-edit
---

<style>ul li {line-height: 1.1}</style>

### ✏️ Staging {#staging}

!!! quote ""
    > This version focuses on internal refactors and simplifications, by removing maintenance-burden features which are better done externally through scripts or library usage, and a website overhaul with [zensical](https://zensical.org/).
    >
    > Reason why it took so long was due side-tracking to deveolp auxiliary projects like [Pyaket](https://pyaket.dev/) for upcoming executable releases, starting to decouple projects from the monorepo life-support and life priorities.

    **Fixes**

    - Fixed a internal resolution doubling bug before the final resize
    - Fix `turbopipe.sync` shouldn't be called when disabled
    - Fixed FFmpeg command line interface options help missing

    **Changes**

    - Swap logger library to [DearLog](https://github.com/BrokenSource/DearLog/) from [Loguru](https://github.com/Delgan/loguru)
    - Make the inpainting mask color white
    - Add experimental Depth Anything v3 estimator option
    - Moved depth estimators to this package from shared library

    **Removals**

    - Remove batch processing support for its many problems and better done in [scripts](https://github.com/BrokenSource/DepthFlow/blob/main/examples/batch.py)
    - Recalled all executable releases until [Pyaket](https://pyaket.dev/) ones are made, within next release
    - Remove upscaler and estimator experimental CLIs

### 📦 v0.9.0 <small>June 2, 2025</small> {#0.9.0}

!!! success ""
    - Convert the project into snake case
    - Overhauled the Readme and the WebUI layout and content
    - Improvements to perceptual quality of the animation presets
    - Add [Upscayl](https://github.com/upscayl/upscayl) as an upscaler option
    - Add a command line interface for all upscalers and depth estimators
    - Fixed drag and drop of files due new lazy loading logic
    - Add stretch detection math on the shader for potential fill-in with gen ai
    - Add colors filters (sepia, grayscale, saturation, contrast, brightness)
    - Add transverse lens distortion filter (intensity, decay options)
    - Overhaul animation system to be more flexible and reliable
    - Reorganize website examples section into their own pages
    - Cached depthmaps are now handled by `diskcache` for safer cross-process
    - Refactor the shader for future include system external usage
    - Simplify how the ray intersections are computed with ray marching
    - Fix how projection rays are calculated, as `steady`, `focus` were slightly wrong
    - Fix base scene duration is now 5 seconds

### 📦 v0.8.0 <small>October 27, 2024</small> {#0.8.0}

!!! success ""
    - Implement batch export logic within the main command line
    - PyTorch is now managed in a top-level CLI entry point
    - Many improvements to the website documentation: Quickstart, examples, and more
    - Added Apple's [DepthPro](https://github.com/apple/ml-depth-pro) as an Depth Estimator option
    - The exported video now properly follows the input image's resolution
    - Loading inputs is now _lazy_, and only happens at module setup before rendering
    - Improved the Readme with community work, quick links, showcase
