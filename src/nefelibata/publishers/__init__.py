from pathlib import Path


class Publisher:
    def publish(root: Path) -> None:
        raise NotImplementedError("Subclasses must implement publish")
