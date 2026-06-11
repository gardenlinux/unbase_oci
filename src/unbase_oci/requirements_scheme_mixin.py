# -*- coding: utf-8 -*-

"""
Dependency scanner based on execution of unbase OCI inside container
"""

from importlib import import_module
from os import PathLike
from pathlib import Path
from typing import Dict
import json

from jsonschema import validate as jsonschema_validate

from .constants import SCHEMES_FILE_JSON_SCHEMA
from .detection import (
    AbstractDependencyHandler,
    AptDependencyHandler,
    AptTreeDependencyHandler,
    FileDependencyHandler,
    PyDependencyHandler,
)


class RequirementsSchemeMixin(object):
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

    def __init__(self) -> None:
        """
        Constructor __init__(DependencyScanner)

        :param unbase_inplace_file: File with required entries used in-place to add
            a list of unbase OCI detected dependencies to

        :since: 0.2.0
        """

        self._external_requirement_handlers: Dict[
            str, type[AbstractDependencyHandler]
        ] = {
            "apt": AptDependencyHandler,
            "apt-tree": AptTreeDependencyHandler,
            "file": FileDependencyHandler,
            "py": PyDependencyHandler,
        }

    def add_scheme(self, scheme: str, py_reference_name: str) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if scheme in self._external_requirement_handlers:
            return None

        py_package, py_class_name = py_reference_name.rsplit(".", 1)
        module = import_module(py_package)
        py_class = getattr(module, py_class_name)

        if not isinstance(getattr(module, py_class), AbstractDependencyHandler):
            raise RuntimeError(
                f"Requirements scheme definition given can not be resolved to a dependency handler: {py_reference_name}"
            )

        self._external_requirement_handlers[scheme] = py_class

    def load_schemes_file(self, schemes_path: str | PathLike[str]) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(schemes_path, Path):
            schemes_path = Path(schemes_path)

        if not schemes_path.exists():
            raise RuntimeError(f"No such file or directory: {schemes_path}")

        schemes = json.loads(schemes_path.read_text())
        jsonschema_validate(schemes, schema=SCHEMES_FILE_JSON_SCHEMA)

        for scheme in schemes:
            self.add_scheme(scheme["scheme"], scheme["handler"])
