"""Config module"""

import json
import os
import pathlib
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).parent


class Config:
    """Config"""

    CONFIG_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), "config.json")

    DEFAULT_CONFIG = {
        "display": True,
        "printing": False,
        "record_timings": True,
        "debug": True,
        "text_debug": False,
        "simple_debug": False,
        "timing_graph": False,
        "max_graph_points": 1000,
        "pixel_scale": 1,
        "display_width": 200,
        "display_height": 200,
        "bits": 32,
        "register_count": 16,
        "ram_size": 1024,
        "stack_size": 1024,
        "graph_update_frequency": 5,
        "batch_size": 1000,
        "window_update_interval": 200,
    }

    def __init__(self):
        self.config = {}

    def load(self) -> None:
        """Load config from file"""

        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = self.DEFAULT_CONFIG

    def save(self) -> None:
        """Save config to file"""

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""

        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set config value"""

        self.config[key] = value
        self.save()
