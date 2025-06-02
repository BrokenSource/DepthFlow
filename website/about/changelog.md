---
icon: material/file-document-edit
---

<style>
    li {margin-bottom: 2px !important;}
    p  {margin-bottom: 2px !important;}
</style>

### ✏️ Staging <small>Unreleased</small> {#next}

!!! example ""
    - Cooking!

### 📦 v0.9.0 <small>June 2, 2025</small> {#0.9.0}

!!! success ""
    - Convert the project into snake case, still have my differences
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
