import sys

from Broken import shell

try:
    import manim
except ImportError:
    shell(sys.executable, "-m", "uv", "pip", "install", "manim")
    import manim


def main():
    ...