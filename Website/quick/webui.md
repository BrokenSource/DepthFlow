---
title: DepthFlow/WebUI
---

✅ On any installation method, you can run `depthflow gradio` to start the web interface. This will open a new tab in your default browser on a local server hosted in your machine:

<div align="center">
    <img src="https://github.com/user-attachments/assets/05b81504-d736-4c95-8e6f-9b4901c9eebd">
</div>

The user interface _should_ be somewhat self-explanatory, and is subject to change.

- 📁 **Input any image** on the top left, optionally upscale it; configure rendering options below and/or change the animations, and hit _"Render"_ to generate a video!

- ♻️ **You can pass** a `depthflow gradio --share` flag to have a temporary _public link_ of your instance, _proxied_ through [**Gradio**](https://www.gradio.app/)'s servers. Do this when hosting for a friend, or if you don't have access to the local network of a remote/rented server!

- ✏️ **Options that** could cause confusion include <kbd>Fit width</kbd> or <kbd>Fit height</kbd>. If you click _fit width_, the _height_ will be calculated to match the image's aspect ratio, e.g.

- 🚧 **Animations** system _will_ change and be improved. For now, enable presets and change their settings on the expandable accordion on the middle of the interface.

{% include-markdown "include/love-short.md" %}
