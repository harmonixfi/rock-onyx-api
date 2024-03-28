# Confidential and proprietary to Salama Systems.
import logging
import pathlib
import sys

import pendulum

_root_logger = logging.getLogger()


def get_log_path(filename: str) -> pathlib.Path:
    if sys.platform == "darwin":
        path = f"~/logs/{filename}.log"
    elif sys.platform == "linux":
        path = f"/app-logs/{filename}.log"
    else:
        path = f"D:\\Working\\Salama\\stl-core\\app-logs\\{filename}.log"

    return pathlib.Path(path).expanduser()


def setup_logging_to_file(
    app: str,
    level: int = logging.INFO,
    *,
    logger: logging.Logger = _root_logger,
    timestamp: bool = True,
) -> pathlib.Path:
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d %(message)s"
    )
    if timestamp:
        filename = f"{app}.{pendulum.now():%Y%m%d.%H%M%S.%f}"
    else:
        filename = app
    log_path = get_log_path(filename)
    file_handler = logging.FileHandler(log_path)
    file_handler.formatter = formatter
    logger.setLevel(level)
    logger.addHandler(file_handler)
    return log_path


def setup_logging_to_console(level=logging.INFO, *, logger: logging.Logger = _root_logger):
    if not sys.stdout.isatty():
        return

    from rich.logging import RichHandler
    from rich.traceback import install

    install(show_locals=True)
    logger.setLevel(level)
    handler = RichHandler(rich_tracebacks=True, level=level, show_time=True)
    logger.addHandler(handler)
