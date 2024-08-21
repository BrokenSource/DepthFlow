from Broken import BrokenProfiler, BrokenTyper
from DepthFlow import DepthScene


def main_webui():
    from DepthFlow.Webui import DepthFlowWebui

    with BrokenProfiler("DEPTHFLOW"):
        DepthFlowWebui().launch()

def main():
    def run():
        DepthScene().cli()
    app = BrokenTyper()
    app.release_repl()
    app.command(run)
    app()

if __name__ == "__main__":
    main()
