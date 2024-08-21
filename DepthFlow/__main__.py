from Broken import BrokenProfiler, BrokenTyper
from DepthFlow import DepthScene


def main_webui():
    from DepthFlow.Webui import DepthWebui

    with BrokenProfiler("DEPTHFLOW"):
        DepthWebui().launch()

def main():
    def run():
        with BrokenProfiler("DEPTHFLOW"):
            DepthScene().cli()
    app = BrokenTyper()
    app.release_repl()
    app.command(run)
    app()

if __name__ == "__main__":
    main()
