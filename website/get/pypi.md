---
title: PyPI
icon: material/language-python
tags:
- Install
- PyPI
---

DepthFlow is available in the Python Package Index (PyPI) via [`depthflow`](https://pypi.org/project/depthflow/) package.

## :simple-astral: With uv {#uv}

Have [astral-sh/uv](https://docs.astral.sh/uv/getting-started/installation/) installed - a modern python manager and runner.

### Script

Create a script with dependencies [syntax file](https://docs.astral.sh/uv/guides/scripts/#running-a-script-with-dependencies) like:

```python
# /// script
# dependencies = [
#   "depthflow>=1.0",
# ]
# ///

from depthflow.scene import DepthScene

scene = DepthScene()
scene.main()
```

Open a terminal in the script directory and run:

```bash
uv run script.py
```

### Direct

Following the concepts of [uv/tools](https://docs.astral.sh/uv/concepts/tools/), you can run it from an ephemeral environment:

```linenums="1"
uvx depthflow main
```

## :material-language-python: With pip {#pip}

Simply install the `depthflow` package, use in your venv, or run its main entry point:

```linenums="1"
python3 -m pip install depthflow
python3 -m depthflow (args)
```
