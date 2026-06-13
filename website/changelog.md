---
title: Changelog
icon: material/file-document-edit
tags:
- About
- Changelog
- Versions
- Legacy
---

<style>ul li {line-height: 1.1}</style>

## Next

!!! danger "Major breaking changes"
    **DepthFlow** is now scoped to be a minimal library-first application, and do it well.

    Features were added without much thought in future maintenance cost, snowballing into making a new release impossible on any internal changes - the only solution was softly starting over, now with experience.

Expect more frequent releases and patches now that I'm actively using it in other projects, and the codebase is easier to maintain. May also reimplement removals in better ways!

<small>**Note**: [Legacy](#legacy) versions will exist for a while, whether you depend or used previous features or code like the WebUI.</small>

### :package: v1.0.0 <small>Developing</small> {#v1.0.0}

!!! quote ""
    For all practical purposes, this is the first _proper release_ of depthflow.

    - Move website to tremeschin.com domain, port contents into [zensical](https://zensical.org/)
    - Remove batch processing support for its many problems and better done in scripts
    - Remove depth estimators cli (can use via library, image formats don't like u16, f32)
    - Remove animation system, now in example scripts and documentation
    - Remove Gradio WebUI for a future rework (looking for better libraries)
    - Remove all upscalers wrappers (out of scope)

## Legacy

!!! warning "Legacy versions may be removed when things stabilize"
    - They were heavily coupled with a monorepo, now independent (reduces package count in PyPI)
    - Unsupported and spaghetti code vs newer releases, maximum Python 3.13 support
    - Thinking in a year or two after [v1.0](#v1.0.0) for removals, extra months for shared library

### :package: v0.9.1 <small>June 29, 2025</small> {#v0.9.1}

!!! quote ""
    - Limit imgui-bundle up to v1.6.3 per breaking changes

!!! quote "Changes ever since that would've been a v0.10, present in v1.0"
    - Fix internal resolution doubling bug before the final resize
    - Fix FFmpeg command line interface options help missing
    - Fix `turbopipe.sync` shouldn't be called when disabled
    - Fix Docs videos missing, now hosted on GitHub user content
    - Moved depth estimators to this package from shared library
    - Swap logger library to [DearLog](https://github.com/BrokenSource/DearLog/) from [Loguru](https://github.com/Delgan/loguru)
    - Make the inpainting mask color green
    - Move to cyclopts cli library over typer

### :package: v0.9.0 <small>June 02, 2025</small> {#v0.9.0}

!!! quote ""
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

### :package: v0.8.0 <small>October 27, 2024</small> {#v0.8.0}

!!! quote ""
    - Implement batch export logic within the main command line
    - PyTorch is now managed in a top-level CLI entry point
    - Many improvements to the website documentation: Quickstart, examples, and more
    - Added Apple's [DepthPro](https://github.com/apple/ml-depth-pro) as an Depth Estimator option
    - The exported video now properly follows the input image's resolution
    - Loading inputs is now _lazy_, and only happens at module setup before rendering
    - Improved the Readme with community work, quick links, showcase

**Note**: Versions started in sync with a monorepo, previous ones aren't worthy.
