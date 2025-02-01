from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


class BrokenHook(MetadataHookInterface):
    def update(self, metadata: dict) -> None:
        path = (Path.cwd()/"_")

        # Attempt to find the monorepo root walking upwards
        while path != (path := path.parent):
            if (version := path/"Broken"/"Version.py").exists():
                exec(version.read_text(), namespace := {})
                version = namespace["__version__"]

                # Set self project version
                metadata["version"] = version

                # Replaces all list items inline
                def patch(items: list[str]) -> None:
                    for (x, item) in enumerate(items):
                        items[x] = item.replace("0.0.0", version)

                # Patch all normal and optional dependencies
                list(map(patch, metadata.get("optional-dependencies", {}).values()))
                patch(metadata.get("dependencies", {}))
                break

        # Path is the system root
        if (path == path.parent):
            print(f"\n(Warning) Couldn't find the BrokenSource monorepo root walking upwards the directory tree from the project at ({Path.cwd()}). Standalone execution isn't supported and will likely fail, as everything is tightly coupled. You can get proper cloning and setup instructions at the website (https://brokensrc.dev/get/source/), see you there!\n")
