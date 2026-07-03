---
title: Camera
icon: octicons/device-camera-video-16
description: Learn how to adjust 3D parallax effects using camera parameters like
  Height, Offset, Steady, Isometric, Dolly, Focus, Quality, Zoom, Center, and Origin.
tags:
- Documentation
- Camera
- Quality
- Height
- Offset
- Steady
- Isometric
- Dolly
- Focus
- Zoom
- Center
- Origin
---

!!! info "Pause looping videos for performance"

This page talks about the parallax projection parameters and their effects. Most are direct matches to the base shader engine [:octicons-package-16: Camera](https://shaders.tremeschin.com/docs/camera/) model, but some like [#steady](#steady) and [#focus](#focus) are complex linear algebra transformations done internally, already managed for you :slight_smile:

## Height

Controls the scale factor of the projection surface growing towards the camera, acting like a global parallax intensity scalar. When depth maps are normalized:

- A value of (0) zero generates no 3D displacements, the surface is flat at z=1.
- A value of (1) one makes the surface's peak be on the same xy plane as the camera.
- Note how in the video, the center doesn't touch the camera, as its relative depth value isn't 1, but the closer bottom edge _"gets below"_ the camera's view - where the peak is.

<video loop controls src="https://github.com/user-attachments/assets/d388e725-2fb9-445e-b51d-3a63d60a6943"></video>

## Offset

Controls the camera position relative to the [#center](#center), generating the parallax effect.

<video loop controls src="https://github.com/user-attachments/assets/ae5f9b47-0fdc-4e78-95e5-49a3cf792429"></video>

Visual changes are proportional to the [#height](#height) parameter, so larger values are required for flatter surfaces to displace the same. Note that this increases the "incident" angle at the opposite sides, creating stretchy regions - see [#isometric](#isometric) for reducing them at the cost of perspective.

Coordinates are normalized vertically and scale horizontally with the aspect ratio:

- A value of y=1 always positions the camera at the upper edge
- For a 16:9 image, 1.77 positions it on the right side.

There's two main operation modes, default being [#sticky](#sticky) (seen on video above):

### Sticky

Just after the flat plane projections are calculated, the camera position is subtracted from the ray intersections, making the background stay fixed in place (camera always looks at the origin).

This is an extremely non-linear transformation; to control what depth stays fixed see [#steady](#steady).

### Tiles

Corrections seen in [#sticky](#sticky) aren't applied in this mode, so offsets makes the camera freely roam around like in most 2.5D games. Since the texture repeats in the shader, using image tiles that seamleslly connect is recommended for this mode, as seen on the video below:

<video loop controls src="https://github.com/user-attachments/assets/09f99bb3-dcee-4d93-a91d-5e723bcf5e2d"></video>

## Steady

Controls the depth plane at which [#offsets](#offset) changes cause no displacement in [#sticky](#sticky) mode.

- A value of (0.0) zero makes the far background always static.
- A value of (0.5) half _"pivots around the middle"_, inverting offsets past it.

<video loop controls src="https://github.com/user-attachments/assets/0f1ad681-9c1d-4b09-b999-88d1c6d44c67"></video>

-> Think about it as an _Offsets Focal Depth._

## Isometric

Controls how much perspective is applied, acting like a planification effect.

<video loop controls src="https://github.com/user-attachments/assets/725927e4-d69a-46dc-a783-9eebbb121e8c"></video>

- A value of (0) zero gives maximum perspective (3D-ness), making all rays originate from the camera's position point, at the cost of more _"sideways"_ indicent angles at the edges.
- A value of (1) one makes all rays parallel, giving a completely flat projection without depth sensation, as if only offsets were applied to thousands of layers in the image (video below).

<video loop controls src="https://github.com/user-attachments/assets/215c4663-d91d-42bd-a984-da27b1bba2df"></video>

Intermediate values are recommended to mitigate strechy regions, reducing how much sideways distortion and/or enchroaching happens. For a better understanding, let's think about the internal angles at which the upper edge operates:

> The camera plane is always at z=0, surface plane at z=1, upper screen edge at y=1. Isometric controls the relative size between both planes, therefore:
>
> - For isometric=1 all rays are parallel, so the incoming angle is 0° at the surface.
> - For isometric=0, a right-triangle of distance 1 and height 1 forms between the ray origin, surface center, and upper screen, so the angle is 45° via isosceles triangle.
> - Intermediate values follow atan(1 - isometric), in fact all cases does.

-> Check this [Desmos](https://www.desmos.com/calculator/owtbbutf27) graph with the formulas.

## Dolly

!!! tip "For the traditional 'dolly zoom' effect, combine it with the [#focus](#focus) parameter."

Sibling of [#isometric](#isometric) virtually doing the same thing, however with different units and may break other parameters projections since it's not a _"natural parameter"_.

Internally, it moves the ray origin plane backwards, so a value of :infinity: is the same as isometric=1.

<video loop controls src="https://github.com/user-attachments/assets/978e6487-de9a-49a4-b14c-a64b77d2acf9"></video>

As far as I know, the conversion factor between the two is given by:

```python
def isometric(dolly: float) -> float:
    return 1 - 1/(1 + dolly)

def dolly(isometric: float) -> float:
    return 1/(1 - isometric) - 1
```

-> Check this [Desmos](https://www.desmos.com/calculator/owtbbutf27) graph with the formulas.

## Focus

Controls the depth plane at which [#isometric](#isometric) changes cause no displacement.

<video loop controls src="https://github.com/user-attachments/assets/bb8643d8-9047-44f2-a96d-46fbe9c47d04"></video>

- Notice how in the video, the green line doesn't move when the `isometric` changes, and the mirroring of perspective directions when crossing this boundary.
- This parameter makes this depth value the surface plane internally.

-> Think about it as an _Isometric Focal Depth._

## Quality

Controls the number of ray marching steps. Lower values increases the algorithm discreteness, causing layers to not blend together in an unwanted "cutout" effect, but increases performance.

<video loop controls src="https://github.com/user-attachments/assets/e25f7fbc-9365-427c-a224-d07924e4e4a1"></video>

Note that a high quality value makes no difference for small offsets, be conservative for speed.

## Zoom

Controls the camera field of view, acting like a digital zoom or cropping.

<video loop controls src="https://github.com/user-attachments/assets/186df0d2-e4b8-470c-9d86-9042d80db0d8"></video>

A value of 1 means the image is fully visible, while a value of 0.5 means a quarter of the image is visible.

## Center

Follows [#offset](#offset) coordinates model, simply offsets the image texture.

<video loop controls src="https://github.com/user-attachments/assets/3cb21f9d-6956-4e0a-9706-3dc44926a2b4"></video>

## Origin

Virtual parameter that controls at which point [#height](#height) changes causes no displacement, and where [#offset](#offset) projections are relative to (as if the camera was above this point). Since the default is zero, the center point of the screen receives this treatment as one expects.

<video loop controls src="https://github.com/user-attachments/assets/f5b043fa-c5f9-494c-bf31-fd41c72c890e"></video>
