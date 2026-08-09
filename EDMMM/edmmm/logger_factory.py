import logging
from logging.handlers import RotatingFileHandler
from os.path import basename, dirname
from pathlib import Path

import config

_plugin_dir = Path(dirname(__file__)).parent
_plugin_name = basename(_plugin_dir)

LOG_DIR = _plugin_dir / "logs"
LOG_FILE = LOG_DIR / "EDMMM.log"
"""Local plugin log, kept next to the plugin instead of EDMC's log folder."""

_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s")
_FORMATTER.default_time_format = "%Y-%m-%d %H:%M:%S"
_FORMATTER.default_msec_format = "%s.%03d"


def __build_logger_for_module() -> logging.Logger:
    """
    Create the logger for this plugin in accordance with the EDMC docs.

    Messages still propagate to EDMC's own log (the logger is a child of
    EDMC's root logger), but a rotating copy is also written to
    <plugin>/logs/EDMMM.log so plugin issues can be inspected without
    digging through EDMC's log folder.
    """
    logger_name = f"{config.appname}.{_plugin_name}"
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.INFO)

    if not any(isinstance(h, RotatingFileHandler) for h in _logger.handlers):
        try:
            LOG_DIR.mkdir(exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=512 * 1024, backupCount=2, encoding="utf8")
            file_handler.setFormatter(_FORMATTER)
            _logger.addHandler(file_handler)
        except Exception:
            # Never let logging setup break the plugin; EDMC's log still works
            pass

    if not _logger.hasHandlers():
        # Standalone use (tests, no EDMC parent handlers): log to stderr
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(_FORMATTER)
        _logger.addHandler(stream_handler)

    return _logger


logger = __build_logger_for_module()
"""
Logger for this Plugin.
"""
