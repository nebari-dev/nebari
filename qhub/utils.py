import time
import os
import contextlib


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f"{prefix} took {time.time() - start_time:.3f} [s]")


@contextlib.contextmanager
def change_directory(directory):
    current_directory = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(current_directory)
