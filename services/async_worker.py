from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable

from PySide6.QtCore import QObject, Signal


class Bridge(QObject):
    success = Signal(object, object)
    failure = Signal(object, object)


class AsyncWorker:
    def __init__(self) -> None:
        self.bridge = Bridge()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run,
            name="PlugPilotAsync",
            daemon=True,
        )
        self.thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(
        self,
        coroutine,
        on_success: Callable[[Any], None],
        on_failure: Callable[[Exception], None],
    ) -> None:
        token = object()

        def success_handler(result_token, result):
            if result_token is token:
                self._disconnect(success_handler, failure_handler)
                on_success(result)

        def failure_handler(result_token, error):
            if result_token is token:
                self._disconnect(success_handler, failure_handler)
                on_failure(error)

        self.bridge.success.connect(success_handler)
        self.bridge.failure.connect(failure_handler)

        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)

        def done(fut):
            try:
                self.bridge.success.emit(token, fut.result())
            except Exception as exc:
                self.bridge.failure.emit(token, exc)

        future.add_done_callback(done)

    def shutdown(self) -> None:
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _disconnect(self, success_handler, failure_handler) -> None:
        try:
            self.bridge.success.disconnect(success_handler)
            self.bridge.failure.disconnect(failure_handler)
        except RuntimeError:
            pass
