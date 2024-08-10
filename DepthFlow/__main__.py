import sys

from Broken import BrokenProfiler
from DepthFlow import DepthScene


def main():
    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli()

def main_webui():
    from DepthFlow.Webui import DepthFlowWebui
    DepthFlowWebui().launch()

if __name__ == "__main__":
    main()
