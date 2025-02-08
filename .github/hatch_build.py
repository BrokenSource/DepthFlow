import os
from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface

path = Path.cwd()

while (path != path.parent):
    if (hook := (path/"Broken"/"Hatch.py")).exists():
        os.environ.setdefault("MONOREPO_ROOT", str(path))
        exec(compile(hook.read_text("utf-8"), hook, "exec"), (scope := {}))
        globals().update(scope)
        break
    path = path.parent
else:
    class DummyHook(MetadataHookInterface):
        def update(self, metadata: dict) -> None:
            pass
