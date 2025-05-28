"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of programmatically batch rendering multiple inputs
"""
from depthflow.scene import DepthScene
from pathlib import Path

def main():
    # Change to your own paths
    INPUTS  = Path("./images").glob("*")
    OUTPUTS = Path("./videos")

    scene = DepthScene(backend="headless")

    for file in Path(INPUTS).glob("*"):
        output = OUTPUTS/file.with_suffix(".mp4").name
        scene.input(image=file)
        scene.main(output=output)

if __name__ == "__main__":
    main()
