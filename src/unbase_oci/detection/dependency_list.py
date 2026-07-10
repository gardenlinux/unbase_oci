# -*- coding: utf-8 -*-

"""
Iterable dependency list of binaries and libraries
"""

from collections import OrderedDict
from ctypes import cdll
from fnmatch import filter as fnfilter
from fnmatch import fnmatch
from logging import getLogger, Logger
from os import PathLike
from pathlib import Path
from typing import Generator, List, Optional

from dlinfo import DLInfo
from elftools.elf.elffile import ELFFile
from macholib.MachO import MachO
from macholib.mach_o import LC_LOAD_DYLIB

from .magic import Magic
from .py_dependency_handler import PyDependencyHandler

from ..constants import (
    DEPENDENCY_LIST_MAX_CACHE_ENTRIES,
    DEPENDENCY_LIST_SUPPORTED_MIME_MAGICS,
)


class DependencyList(dict[str, List[str]]):
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

    _cache: OrderedDict[str, List[str]] = OrderedDict()

    def __init__(
        self,
        exclude_globs: List[str],
        filter_supported: bool = True,
        python_env_self_dependencies: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Constructor __init__(DependencyList)
        @TODO: Fix me

        :since: 0.2.0
        """

        dict.__init__(self)

        if logger is None or not logger.hasHandlers():
            logger = getLogger("unbase_oci.detection")

        self._exclude_globs = exclude_globs
        self._filter_supported = filter_supported
        self._logger = logger
        self._python_env_self_dependencies = python_env_self_dependencies

    def __iter__(self) -> Generator[str]:
        """
        python.org: Return an iterator object.

        :return: (object) Iterator object
        :since:  v0.2.0
        """

        for key in dict.__iter__(self):
            is_excluded = False

            for exclude_glob in self._exclude_globs:
                if (
                    fnmatch(key, exclude_glob)
                    or len(fnfilter(self[key], exclude_glob)) > 0
                ):
                    self._logger.debug(f"Dependency '{key}' excluded")

                    is_excluded = True
                    break

            if is_excluded:
                continue

            yield key

    def add(self, file_path: str | PathLike[str], dependencies: List[str] = []) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if file_path.exists() and not file_path.is_dir() and str(file_path) not in self:
            absolute_file_path = self._add_symlinks_and_get_real_path(file_path)
            absolute_file_path_str = str(absolute_file_path)

            self[absolute_file_path_str] = dependencies
            self._set_cached_key(absolute_file_path_str, dependencies)

    def _add_from_cached_key(self, key: str) -> bool:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        cache = self.__class__._cache

        if key not in cache:
            return False

        self[key] = cache[key]

        for dep_path in cache[key]:
            self._add_from_cached_key(dep_path)

        cache.move_to_end(key)
        return True

    def _add_symlinks_and_get_real_path(self, file_path: Path) -> Path:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        constructed_path = Path()

        for part in file_path.parts:
            partial_path = constructed_path.joinpath(part)

            if partial_path.is_symlink():
                self[str(partial_path)] = []
                partial_path = partial_path.readlink()

                if not (
                    partial_path.is_absolute()
                    or partial_path.is_relative_to(constructed_path)
                ):
                    partial_path = (
                        constructed_path.absolute() / partial_path
                    ).resolve()

                constructed_path = self._add_symlinks_and_get_real_path(partial_path)
            else:
                constructed_path = partial_path

        return constructed_path.absolute()

    def _set_cached_key(self, key: str, value: List[str]) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        cache = self.__class__._cache

        if len(cache) > DEPENDENCY_LIST_MAX_CACHE_ENTRIES:
            cache.popitem(False)

        cache[key] = value

    def detect(self, file_path: str | PathLike[str]) -> bool:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        absolute_file_path = self._add_symlinks_and_get_real_path(file_path)
        absolute_file_path_str = str(absolute_file_path)

        if absolute_file_path_str in self or self._add_from_cached_key(
            absolute_file_path_str
        ):
            return True

        magic = Magic()
        file_mime_magic = magic(absolute_file_path)

        self[absolute_file_path_str] = []

        if (
            self._filter_supported
            and file_mime_magic not in DEPENDENCY_LIST_SUPPORTED_MIME_MAGICS
        ):
            self._logger.debug(
                f"'{absolute_file_path}' has mime type: {file_mime_magic}"
            )

            return True

        if (
            file_mime_magic == "text/x-script.python"
            and not self._python_env_self_dependencies
        ):
            return True

        self._logger.debug(
            f"Detecting dependencies for '{absolute_file_path}' ({file_mime_magic})"
        )

        result = True

        if file_mime_magic in DEPENDENCY_LIST_SUPPORTED_MIME_MAGICS:
            match file_mime_magic:
                case "application/x-executable" | "application/x-pie-executable":
                    result = result and self._detect_elf_dependencies(
                        absolute_file_path
                    )
                case "application/x-mach-binary":
                    result = result and self._detect_mach_dependencies(
                        absolute_file_path
                    )
                case "text/x-script.python":
                    result = result and self._detect_py_dependencies(absolute_file_path)
                case _:
                    return False

        if result:
            self._set_cached_key(absolute_file_path_str, self[absolute_file_path_str])

        return result

    def _detect_elf_dependencies(self, absolute_file_path: Path) -> bool:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        elf_file = ELFFile.load_from_path(absolute_file_path)
        section = elf_file.get_section_by_name(".dynamic")

        result = True

        for tag in section.iter_tags("DT_NEEDED"):
            dep_path = DLInfo(cdll.LoadLibrary(tag.needed)).path

            self[str(absolute_file_path)].append(dep_path)
            result = result and self.detect(dep_path)

        return result

    def _detect_mach_dependencies(self, absolute_file_path: Path) -> bool:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        macho = MachO(absolute_file_path)

        result = True

        for header in macho.headers:
            for load_command, command_data, data in header.commands:
                if load_command.cmd == LC_LOAD_DYLIB:
                    dylib_file = data.strip(b"\x00").decode("utf-8")

                    if Path(dylib_file).is_absolute():
                        dep_path = dylib_file
                    else:
                        dep_path = DLInfo(cdll.LoadLibrary(dylib_file)).path

                    self[str(absolute_file_path)].append(dep_path)
                    result = result and self.detect(dep_path)

        return result

    def _detect_py_dependencies(self, absolute_file_path: Path) -> bool:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        handler = PyDependencyHandler(self, self._logger)
        handler.scan_for_requirement_uri(f"py:///{absolute_file_path}")

        return True
