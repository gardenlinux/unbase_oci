# -*- coding: utf-8 -*-

"""
Dependency scanner based on execution of unbase OCI inside container
"""

from logging import getLogger, Logger
from os import PathLike, chdir
from pathlib import Path
from typing import List, Optional
import json

from .detection import DependencyList
from .requirements_scheme_mixin import RequirementsSchemeMixin


class DependencyScanner(RequirementsSchemeMixin):
    """
    Dependency scanner detects supported dependent files based on execution of
    unbase OCI inside the target container.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    def __init__(
        self,
        unbase_inplace_file: str | PathLike[str],
        python_env_self_dependencies: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Constructor __init__(DependencyScanner)

        :param unbase_inplace_file: File with required entries used in-place to add
            a list of unbase OCI detected dependencies to

        :since: 0.2.0
        """

        RequirementsSchemeMixin.__init__(self)

        if not isinstance(unbase_inplace_file, Path):
            unbase_inplace_file = Path(unbase_inplace_file)

        inplace_content = json.loads(unbase_inplace_file.read_text())

        if logger is None or not logger.hasHandlers():
            logger = getLogger("unbase_oci")

        self._dependencies: List[str] = []
        self._exclude_globs = inplace_content["exclude_globs"]
        self._logger = logger
        self._python_env_self_dependencies = python_env_self_dependencies
        self._requirements = inplace_content["requirements"]
        self._symlink_dependencies: List[str] = []
        self._unbase_inplace_file = unbase_inplace_file

    def add_dependency(self, dependency: str | PathLike[str]) -> None:
        """
        Adds a dependent file to the list if not already added.

        :param dependency: Dependent file

        :since: 0.2.0
        """

        dependency_str = (
            str(dependency) if isinstance(dependency, PathLike) else dependency
        )

        if dependency_str not in self._dependencies:
            self._dependencies.append(dependency_str)

    def add_symlink_dependency(self, dependency: str | PathLike[str]) -> None:
        """
        Adds a dependent, symlinked file to the list if not already added.

        :param dependency: Dependent file

        :since: 0.2.0
        """

        if not isinstance(dependency, Path):
            dependency = Path(dependency)

        if not dependency.is_symlink():
            raise RuntimeError(f"Dependent file given is not a symlink: '{dependency}'")

        dependency_str = str(dependency)

        if dependency_str not in self._symlink_dependencies:
            self._symlink_dependencies.append(dependency_str)

    def _handle_external_requirement(self, requirement_uri: str) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        dependency_list = DependencyList(
            self._exclude_globs,
            python_env_self_dependencies=self._python_env_self_dependencies,
        )

        requirement_data = requirement_uri.split(":///", 1)

        handler_class = self._external_requirement_handlers[requirement_data[0]]
        handler = handler_class(dependency_list, logger=self._logger)

        handler.scan_for_requirement_uri(requirement_uri)

        for file_path in dependency_list:
            if Path(file_path).is_symlink():
                self.add_symlink_dependency(file_path)
            else:
                self.add_dependency(file_path)

    def scan(self) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        for requirement in self._requirements:
            try:
                if ":///" in requirement:
                    self._handle_external_requirement(requirement)
                else:
                    self.scan_requirement_for_dependencies(requirement)
            except RuntimeError as exc:
                # @TODO: Fix me
                print(exc)

        dependencies = []

        for dependency in sorted(self._dependencies):
            is_symlinked = False

            for symlink in self._symlink_dependencies:
                if Path(dependency).is_relative_to(symlink):
                    is_symlinked = True
                    break

            if not is_symlinked:
                dependencies.append(dependency)

        self._unbase_inplace_file.write_text(
            json.dumps(
                {
                    "requirements": self._requirements,
                    "exclude_globs": self._exclude_globs,
                    "dependencies": dependencies,
                    "symlink_dependencies": self._symlink_dependencies,
                }
            )
        )

    def scan_requirement_for_dependencies(self, requirement: str) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        cwd_path = Path.cwd()
        requirement_path = Path(requirement)

        if not requirement_path.exists():
            raise RuntimeError(f"No such file or directory: {requirement}")

        if requirement_path.is_dir():
            try:
                chdir(requirement_path.absolute())

                for entry in requirement_path.glob("**/*"):
                    if not entry.is_dir():
                        self._scan_file_for_dependencies(entry)
            finally:
                chdir(cwd_path.absolute())
        else:
            self._scan_file_for_dependencies(requirement_path)

    def _scan_file_for_dependencies(self, requirement_path: Path) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        dependency_list = DependencyList(
            self._exclude_globs,
            python_env_self_dependencies=self._python_env_self_dependencies,
        )

        dependency_list.detect(requirement_path)

        for file_path in dependency_list:
            if Path(file_path).is_symlink():
                self.add_symlink_dependency(file_path)
            else:
                self.add_dependency(file_path)
