# -*- coding: utf-8 -*-

"""
Mime magic abstraction layer
"""

from os import PathLike
from pathlib import Path

from pure_magic_rs import MagicDb


class Magic(object):
    """
    Magic abstracts the underlying mime magic detection for portability.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    _MAGIC_DB = MagicDb()

    def __init__(self) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        pass

    def __call__(self, file_path: str | PathLike[str]) -> str:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise RuntimeError(f"File or directory does not exist: '{file_path}'")
        elif file_path.is_dir():
            return "text/directory"
        elif file_path.is_file():
            return self._detect_for_path(file_path)
        elif file_path.is_block_device():
            return "x-inode/blockdevice"
        elif file_path.is_char_device():
            return "x-inode/chardevice"
        elif file_path.is_fifo():
            return "x-inode/fifo"
        elif file_path.is_socket():
            return "x-inode/socket"

        raise RuntimeError(f"Magic does not support file detection for '{file_path}'")

    def _detect_for_path(self, file_path: Path) -> str:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        result = Magic._MAGIC_DB.best_magic_file(file_path)

        if result.mime_type is None:
            raise RuntimeError(f"Failed to detect mime type for '{file_path}'")

        return result.mime_type  # type: ignore[no-any-return]
