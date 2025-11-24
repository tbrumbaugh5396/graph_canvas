"""
Simple signal implementation for event handling.
"""


from typing import Callable


class Signal:
    """Simple signal implementation for event handling."""

    def __init__(self):
        self.callbacks = []

    def connect(self, callback: Callable):
        """Connect a callback to this signal."""

        self.callbacks.append(callback)

    def disconnect(self, callback: Callable):
        """Disconnect a callback from this signal."""

        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def emit(self, *args, **kwargs):
        """Emit the signal, calling all connected callbacks."""

        for callback in self.callbacks:
            callback(*args, **kwargs)
