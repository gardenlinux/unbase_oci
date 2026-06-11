# -*- coding: utf-8 -*-

"""
Iterable dependency list of Python traversables
"""

from collections.abc import Iterable, Iterator
from importlib import import_module
from logging import getLogger, Logger
from os import PathLike
from pathlib import Path
from typing import Generator, List, Optional
import ast
import sys


class PyPermanentList(Iterable[Path]):
    """
    @TODO: Fix me

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    _list: List[Path] = list()

    def __init__(
        self,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Constructor __init__(PyPermanentList)
        @TODO: Fix me

        :since: 0.2.0
        """

        Iterable.__init__(self)

        if logger is None or not logger.hasHandlers():
            logger = getLogger("unbase_oci.detection")

        self._logger = logger

    def __iter__(self) -> Iterator[Path]:
        """
        python.org: Return an Iterable object.

        :return: (object) Iterable object
        :since:  v0.2.0
        """

        return iter(self.__class__._list)

    def detect(self, file_path: str | PathLike[str]) -> List[str]:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        absolute_file_path = file_path.absolute()
        file_list = self.__class__._list

        if absolute_file_path in file_list or file_path.suffix.lower() != ".py":
            return []

        try:
            py_module = ast.parse(file_path.read_text(), filename=file_path.name)
        except Exception as exc:
            self._logger.error(f"Failed to parse Python file '{file_path}': {exc}")
            return []

        py_packages = []

        for ast_node in ast.walk(py_module):
            if isinstance(ast_node, ast.Import):
                for alias in ast_node.names:
                    if alias.name not in py_packages:
                        py_packages.append(alias.name)
            elif isinstance(ast_node, ast.ImportFrom):
                if ast_node.level == 0 and ast_node.module:
                    if ast_node.module not in py_packages:
                        py_packages.append(ast_node.module)

        if absolute_file_path not in file_list:
            file_list.append(absolute_file_path)

        py_files = []

        for py_file in self._get_packages_files(py_packages):
            if py_file not in py_files:
                py_files.append(py_file)

        return sorted(py_files)

    def _get_packages_files(self, py_packages: List[str]) -> Generator[str]:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        for py_package in py_packages:
            try:
                py_module = (
                    sys.modules[py_package]
                    if py_package in sys.modules
                    else import_module(py_package)
                )

                if getattr(py_module, "__file__", None) is None:
                    continue

                yield py_module.__file__  # type: ignore[misc]

                for py_file in self.detect(py_module.__file__):  # type: ignore[arg-type]
                    yield str(py_file)
            except Exception as exc:
                self._logger.warn(
                    f"Failed to detect Python package {py_package}: {exc}"
                )
