---
title: DepthFlow/Parameters
---

<b><span class="the">T</span>his page</b> focus on all shader-related parameters, and how they affect the final image (in practical terms). The main goal is for helping you to understand how to work with the software and parametrize it to your needs, create your own animations, and more.

- For rendering and exporting parameters, see the [**ShaderFlow**](site:/shaderflow) page ✨
- For understanding the math, see the [**Foundations**](site:/depthflow/learn/foundations) page 📜

<hr>

All parameters are controlled within the [**state dictionary**](https://github.com/BrokenSource/DepthFlow/blob/main/DepthFlow/State.py) class, acessible by:

```python
from DepthFlow import DepthScene

scene = DepthScene()
scene.state.height = 0.3
scene.state.offset_x = 1
```

Or settable by the command line as a animation component:

```python title="Terminal"
# Note: This will only create a static image
depthflow config --height 0.3 --offset-x 1 main
```

However, they are best used within the `.update()` method for creating animations:

```python
import math

class YourScene(DepthScene):
    def update(self):
        self.state.offset_x = 0.3 * math.sin(self.cycle)
```

Internally, they are used and sent when the render method is called for the shader, which non-surprisingly happens in the main event loop of the Scene, after all `.update()`'s.

Directly controlling those makes more sense when managing the code within Python (and bypassing the animation system, which essentially does the same thing) for writing custom animations and more advanced interactions or behaviors.


## Parallax

This section is about the **core parameters** of DepthFlow.

- **Important**: When parameters refers to depth values, the value is _normalized_. A `static` value of $0.5$, with a `height` of $0.3$ means the perceptual `static` values is at $0.15$, (e.g.).

- **Important**: Depth values of zero are the _farthest_ point, and values of one the _closest_.

- **Note**: The suggested ranges aren't enforced, but what makes sense in most cases.

<!-- ------------------------------------------------------------------------------------------- -->

### Height

> **Type:** `float`, **Range:** `[0, 1]`

<b><span class="the">T</span>he</b> `height` parameter defines the **peak height of the projected surface** at `depth=1`. It can be thought as the {==**effect's global intensity**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/height-varying.mp4"></video>

!!! quote "It's arguably the **most important parameter**, virtually nothing happens without it"

- A value of 0 means the surface is flat, while a value of 1 means the surface's peak is on the same $xy$ screen plane as the camera.

- Notice how in the video, the center doesn't touch the camera, as its `depth` value isn't $1$, but the closer bottom edge _"gets below"_ the camera's view.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Offset

> **Type:** `Tuple[float, float]`, **Alias:** `offset_x`, `offset_y`, **Range:** `[-2, 2]`

<b><span class="the">T</span>he</b> `offset` parameter defines the **parallax displacement** of the projected surface. It can be thought as the {==**camera's position**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/offset-x-varying.mp4"></video>

!!! quote "This is the easiest way to add **'natural' movement** to the scene"

- A value of 0 in a component means the surface and camera are centered, other values meaning depends on other parameters and the aspect ratio, _it's a bit experimental._

- This parameter isn't a _"camera displacement"_ you might expect:
    1. That would simply move the image around without changing the perspective, which is what the [**`center`**](#center) parameter does.
    2. The camera always _"looks"_ to the image (`origin` parameter) by adding an opposite bias to the ray's projection on how much the image is displaced.

As you might expect, setting $x=cos(t)$ and $y=cos(t)$ parameter to follow a circular motion, will create a _"orbiting"_ effect around the center of the image.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/offset-xy-varying.mp4"></video>

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Static

> **Type:** `float`, **Range:** `[-1, 1]`

<b><span class="the">T</span>he</b> `static` parameter defines the **depth at which no offsets happen**. It can be thought as the {==**offsets focal depth**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/static-varying.mp4"></video>

!!! quote "It's a great way of adding **subtle background movement** or **orbiting around a point**"

- Notice how in the video, the orange line doesn't move when the `offset` changes, and the mirroring of relative directions when crossing this boundary.

- This parameter makes the ray projections _"pivot"_ around this depth value internally.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Isometric

> **Type:** `float`, **Range:** `[0, 1]`

<b><span class="the">T</span>he</b> `isometric` parameter defines **how much perspective is applied**. It can be thought as the {==**planification effect**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/isometric-varying.mp4"></video>

!!! quote "It's the best way to **mitigate edge or stretching distortions**, at the cost of the 3D-ness of the video"

- A value of 0 means full perspective projection, while a value of 1 means the image is projected as if it was isometric (all rays are parallel).
    1. This completely negates the `height` parameter at `isometric=1`

- This parameter makes effect more _"flat"_ and _"2D"_, in fact, a value of 1 turns offsets into a simple translation. A value of 0.5 is often recommended.

<hr>

Notice how in the video below the offsets are _"flattened"_, as if there was one layer per depth value and it was simply displaced in the $xy$ plane. Consequently, more of the image is visible, as the peak values don't race towards the camera as much, at the cost of being _flat_.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/isometric-flat.mp4"></video>

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Dolly

> **Type:** `float`, **Range:** `[0, 10]`

<b><span class="the">T</span>he</b> `dolly` parameter defines the **camera's distance from the image**. It's basically the same as the {==**isometric effect**==} parameter, but with different _(natural)_ units.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/dolly-varying.mp4"></video>

!!! quote "It's a great way for a **more natural isometric** effect control"

- As you move away to objects, they appear more isometric, that's the reason why your face looks unnatural in close-up selfies.
- A `dolly` value of 0 is the same as `isometric=0`
- A `dolly` value of $\infty$ is the same as `isometric=1`

As far as I know, the convertion factor between the two is given by:

$$
\text{isometric} = 1 - \frac{1}{1 + \text{dolly}}
$$

For the traditional 'dolly zoom' effect, combine it with the [**`focus`**](#focus) parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/dolly-focus-varying.mp4"></video>


<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Focus

> **Type:** `float`, **Range:** `[-1, 1]`

<b><span class="the">T</span>he</b> `focus` parameter defines the **static depth on isometric changes**. It can be thought as the {==**isometric focal depth**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/focus-varying.mp4"></video>

!!! quote "It's a great way to **add drama** to the scene, or **give attention** to an object"

- Notice how in the video, the orange line doesn't move when the `isometric` changes, and the mirroring of perspective directions when crossing this boundary.

- This parameter makes this depth value the $z=1$ plane internally.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Zoom

> **Type:** `float`, **Range:** `(0, 1]`

<b><span class="the">T</span>he</b> `zoom` parameter defines the **camera's field of view**. It can be thought as the {==**you-know-it**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/zoom-varying.mp4"></video>

!!! quote "It's a great way to **crop** the image"

- A value of 1 means the image is fully visible, while a value of 2 means a quarter of the image is visible.

- This is a _"digital zoom"_, it simply stretches the coordinates internally.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Invert

> **Type:** `float`, **Range:** `[0, 1]`

<b><span class="the">T</span>he</b> `invert` parameter **interpolates between 0=far and 1=near and the opposite**. It can be thought as the {==**depth inversion**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/invert-varying.mp4"></video>

!!! quote "This parameter is mostly useful when the input depth map is inverted"

- A value of 0.5 flattens the depth map and nothing happens, while a value of 1 inverts the depth map. Middle values _can be thought as softening_ the depthmap.

- It wraps the surface inside-out when the value is above 0.5, and a lot of encroaching will happen, as the background is now the foreground.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

### Center

> **Type:** `Tuple[float, float]`, **Range:** `([-ar, ar], [-1, 1])`

<b><span class="the">T</span>he</b> `center` parameter defines the **center of the image**. It can be thought as the {==**raw offset**==} parameter.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/center-varying.mp4"></video>

!!! quote "This is the easiest way to **move the image around**"

- A value of 0 in a component means the image is centered, other values applies a direct offset to the contents of the image.

- This parameter is a _"camera displacement"_ you might expect, nothing fancy.

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

        <!-- """Focal point of the offsets, *as if* the camera was above this point""" -->
### Origin

> **Type:** `Tuple[float, float]`, **Range:** `([-ar, ar], [-1, 1])`

<b><span class="the">T</span>he</b> `origin` parameter defines the **center point of offsets**. It can be thought  {==**as if the camera was above this point**==} , without moving it.

<video loop autoplay controls src="https://assets.brokensrc.dev/depthflow/learn/parameters/origin-varying.mp4"></video>

!!! quote "This is a good way to focus on a specific part of the image while feeling off-center"

- The value sets _"the origin"_ of offsets to the projections of the image.

- It is also the value at which height changes only causes zooming

<!-- ------------------------------------------------------------------------------------------- -->

<hr class="thick-hr"/>

## Depth of Field

!!! warning "🚧 Work in Progress 🚧"

## Vignette

!!! warning "🚧 Work in Progress 🚧"
