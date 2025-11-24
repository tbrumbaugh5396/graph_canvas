"""
Manager for persisting zoom-related UI settings (input mode, sensitivity).
"""

import os
import json
from typing import Literal


ZoomMode = Literal['wheel', 'touchpad', 'both']


class ZoomManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_file = os.path.join(base_dir, 'config', 'zoom.json')
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # Defaults
        self._mode: ZoomMode = 'wheel'
        self._sensitivity: float = 1.0

        self.load()

    def load(self) -> None:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    mode = str(data.get('mode', 'wheel')).lower()
                    if mode in ('wheel', 'touchpad', 'both'):
                        self._mode = mode  # persist exactly
                    else:
                        self._mode = 'wheel'
                    sens = float(data.get('sensitivity', 1.0))
                    # Clamp sensitivity to reasonable range
                    self._sensitivity = max(0.1, min(5.0, sens))
        except Exception as e:
            print(f"Error loading zoom settings: {e}")

    def save(self) -> None:
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'mode': self._mode,
                    'sensitivity': self._sensitivity,
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving zoom settings: {e}")

    def get_mode(self) -> ZoomMode:
        return self._mode

    def set_mode(self, mode: str) -> None:
        mode = str(mode).lower()
        self._mode = mode if mode in ('wheel', 'touchpad', 'both') else 'wheel'
        self.save()

    def get_sensitivity(self) -> float:
        return self._sensitivity

    def set_sensitivity(self, value: float) -> None:
        try:
            sens = float(value)
        except Exception:
            sens = 1.0
        self._sensitivity = max(0.1, min(5.0, sens))
        self.save()


