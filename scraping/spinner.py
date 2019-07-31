from __future__ import annotations
import sys
import time
import threading

from typing import Generator, Iterator


class Spinner:
    """
    creates a spinning wheel on command line
    """
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor() -> Generator[Iterator[str]]:
        while 1:
            for cursor in '|/-\\': yield cursor

    def __init__(self, delay=None) -> None:
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self) -> None:
        while self.busy:
            sys.stdout.write(next(self.spinner_generator) + '  ')
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b\b\b')
            sys.stdout.flush()

    def __enter__(self) -> None:
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb) -> bool:
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False
