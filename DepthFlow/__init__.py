import DepthFlow.Resources as DepthFlowResources
from Broken import BrokenProject

DEPTHFLOW_ABOUT = """
🌊 Image to → 2.5D Parallax Effect Video. A Free and Open Source ImmersityAI alternative.\n

Usage: All commands have a --help option with extensible configuration, and are chained together

[yellow]Examples:[/yellow]
• Simplest:    [bold blue]depthflow[/bold blue] [blue]main[/blue] [bright_black]# Realtime window, drag and drop images![/bright_black]
• Your image:  [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image.png [blue]main[/blue]
• Exporting:   [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image.png [blue]main[/blue] -o ./output.mp4
• Upscaler:    [bold blue]depthflow[/bold blue] [blue]realesr[/blue] --scale 2 [blue]input[/blue] -i ./image.png [blue]main[/blue] -o ./output.mp4
• Convenience: [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image16x9.png [blue]main[/blue] -h 1440 [bright_black]# Auto calculates w=2560[/bright_black]
• Estimator:   [bold blue]depthflow[/bold blue] [blue]dav2[/blue] --model large [blue]input[/blue] -i ~/image.png [blue]main[/blue]
• Post FX:     [bold blue]depthflow[/bold blue] [blue]dof[/blue] -e [blue]vignette[/blue] -e [blue]main[/blue]

[yellow]Notes:[/yellow]
• A value of --ssaa between 1.5, 2.0 is recommended for final exports, real time uses 1.2
• The [bold blue]main[/bold blue]'s --quality preset gives little to no improvement for small movements
• The rendered video loops perfectly, the period is the main's --time
• The [bold blue]config[/bold blue] command [bold red]must[/bold red] come before any other presets commands
• The [bold blue]input[/bold blue] command [bold red]must[/bold red] come after [bold blue]upscalers[/bold blue] and [bold blue]estimators[/bold blue]
• The last command [bold red]must[/bold red] be [bold blue]main[/bold blue] for running the scene
"""

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
    ABOUT=DEPTHFLOW_ABOUT,
)

from DepthFlow.Scene import DepthScene
