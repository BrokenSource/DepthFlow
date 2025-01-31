---
title: DepthFlow/Foundations
---

!!! warning "🚧 Work in Progress 🚧"
    Many missing parts, mostly sketching ideas and structure.

This page describes _in depth_[^pun] the DepthFlow project in a paper-like format

[^pun]: Pun intended 🙂

> **Note**: This is a mostly technical write-up with notable trivia, and it's not necessary to understand the math or history to use it. For what you should know, see [**Parameters**](site:/depthflow/learn/parameters).

<hr>

<div align="center" class="paper-title">
    <h2>DepthFlow: A fully featured steep parallax algorithm</h2>
</div>

## Introduction

<b><span class="the">D</span>epthFlow</b> is a software that generates 3D parallax effect videos from images and their depthmaps. This is done by projecting the image in 3D space and rendering from a camera's perspective, with many different parameters that can vary over time.

The code heavily relies on the [**ShaderFlow**](site:/shaderflow){:target="_blank"} engine, providing high level abstractions and utilities such as exporting videos, camera modeling, and more. Technically speaking, DepthFlow is a ShaderFlow spin-off, so does other projects like [**Pianola**](site:/pianola){:target="_blank"} and [**SpectroNote**](site:/spectronote){:target="_blank"}, where the [**main implementation**](https://github.com/BrokenSource/DepthFlow/blob/main/DepthFlow/Resources/Shaders/DepthFlow.glsl){:target="_blank"} is a feature simple, not-so-long but dense [**GLSL**](https://en.wikipedia.org/wiki/OpenGL_Shading_Language){:target="_blank"} shader[^glsl].

[^glsl]: As such, it can be easily ported to other shading languages or platforms, such as [**WebGL**](https://en.wikipedia.org/wiki/WebGL){:target="_blank"}, [**HLSL**](https://en.wikipedia.org/wiki/High-Level_Shading_Language){:target="_blank"}, or [**Metal**](https://en.wikipedia.org/wiki/Metal_(API)){:target="_blank"}.


### Motivation

The original idea for DepthFlow came from a desire to generate filler content and/or more interesting image inserts in videos[^im-not-an-editor]. I happened to be coding a music visualizer / shader infrastructure project for a couple of years, and I took the opportunity to side develop it.

[^im-not-an-editor]: I'm not a content producer myself, but a couple of close or ex-friends are/were

A year later, its applications proved to be much more versatile than I initially thought. It can be used for artistic purposes, automated channels, stock footage, wallpapers, music visualizers, commercials, web design, you name it. Apart from those, it would have been great to have a **Free and Open Source** tool, forever available, for this kind of task.


### Objective

The end goal is to generate this projected image that an observer (camera) would see, _as if_ it was looking from some point $O$ in space, towards the scene.

The inputs involved are:

1. A **source image** that we want to project in 3D space;
2. Its **depth map**[^depthmaps], defining the surface topology.
3. A set of **camera parameters** defining the perspective.
4. Additional resolution, rendering instructions.

[^depthmaps]: Depthmaps are grayscale images (often colorized when presented) that provides relative (normalized) or absolute (value) distances of each pixel from the camera's perspective. Personally speaking, it's more natural to work with (dark=far, bright=near) convention.




## Mathematics

<span class="the">T</span>his section will focus on the heuristics and analytics of the DepthFlow algorithm. We'll go through the main concepts and the math behind them, working with a simplified version of the problem first, and then expanding to the full implementation. I'll provide both the intuition and the formalism, as well as visualizations with [**Manim**](https://www.manim.community){:target="_blank"} ✨

Before you continue, this will involve **a lot of linear algebra**, and I highly recommend learning the basics with [**The Essence of Linear Algebra**](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) series by [**3Blue1Brown**](https://www.3blue1brown.com/).

### The problem

At first, I was overwhelmed by the complexity of the problem. Imagine-, you have a camera ray's origin and direction, and want to find a _precise intersection_ with a certain _surface_ with its topology defined by the depthmap. A couple of natural questions or facts are:

- The method must be discrete, as finding roots would be very expensive[^roots],
- Then, how to find the closest distance to any point for ray marching?
- How to reduce artifacts by the discretization process?
- Is ray marching even the way to approach this?
- How to make it efficient and fast?

[^roots]: If not impossible, depthmap being a high degree polynomial, requiring computational methods on the GPU

In a way, some level of brute forcing is necessary, but we can make it smart. Another thing to realize is that the problem of **finding the intersections** is **totally independent** from the **projection parameters**. The parameters will define what the camera sees (ray origin and target), then it's just a matter of finding intersections with the scene and sampling.

> **Note**: It's possible to create a 3D mesh from the depthmap, and use standard rasterization for the effect. However, rendering this many quads would be [**very expensive**](https://www.youtube.com/watch?v=hf27qsQPRLQ){:target="_blank"}, and a lot of non-linearity would be lost or hard to implement in the Euclidean space we'll see later.

A key insight is to realize that the problem isn't inherently 3D, but 2D. The projection intersection will **only ever happen** _"below[^below]"_ the path a ray takes. Calculate for all, we're set.

[^below]: As if the projection plane was the ground; in a more formal way, the plane defined by the image's plane normal vector, and the ray direction of the camera.


### Definitions

For that, let's start defining the problem from basic, reasonable assumptions:

- The image is centered on the $xy$ screen plane at $z = 1$ (forward)
- The camera is at the origin $(0, 0, 0)$, looking forward $(0, 0, 1)$
- The depthmap uses a (0=far) (1=near) convention
- The camera uses [**this modelling**](site:/shaderflow/learn/camera){:target="_blank"}

And additional

- The image's plane height grows towards the camera ($-z$)
- The depthmap is scaled by a peak height $h$

With only that, we can look at a 2D slice and solve the simplified problem!

!!! note "For more information on the coordinate system details or choice, see [**here**](site:/shaderflow/learn/camera){:target="_blank"}"


### Intersections

This is the simpler part of the problem. The camera's position and looking target will define a ray origin $O$ and a target $T$; consequently a direction vector

$$\vec{d} = T - O$$
