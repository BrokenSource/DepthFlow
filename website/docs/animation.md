---
title: Animation
icon: material/animation-play
description: Create 3D parallax animations by extending the DepthScene class to modify
  Camera parameters over time using temporal and projection variables.
tags:
- Documentation
- Animations
---

For creating your animation with DepthFlow, the recommended method is via [#extending](#extending) the main Scene class, and writing a custom update method changing [:octicons-device-camera-video-16: Camera](./camera.md) parameters over time.

## Extending

Import the main class, create a new one inheriting from it, write an `update` method:

```python title="Circle animation example"
from depthflow.scene import DepthScene

class MyAnimation(DepthScene):
    def update(self):
        self.state.offset = (
            math.cos(self.cycle),
            math.sin(self.cycle),
        )
```

You can use many temporal parameters such as:

!!! quote ""
    === ":octicons-package-16: tau"
        Normalized time from 0-1 relative to total duration.
    === ":octicons-package-16: cycle"
        Normalized time from 0-2pi relative to total duration.
    === ":octicons-package-16: time"
        Elapsed time in seconds since the start of the animation.
    === ":octicons-package-16: frame"
        Current frame count since the start of the animation.

See [:octicons-video-16: Exporting](./exporting.md) for realtime previews or encoding a video file.

## Presets

!!! warning "DepthFlow will include a simple animation system in a future release."
    - For now, check the [Examples](https://github.com/BrokenSource/DepthFlow/tree/main/examples) directory on GitHub in how the [:octicons-device-camera-video-16: Camera](./camera.md) example videos are made, and the previous v0.9 hardcoded presets in the update method.
