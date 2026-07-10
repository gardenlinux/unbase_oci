# -*- coding: utf-8 -*-

"""
Dependency handler for apt:/// of unbase OCI
"""

from logging import Logger
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

from .abstract_dependency_handler import AbstractDependencyHandler
from .py_permanent_list import PyPermanentList


class PyDependencyHandler(AbstractDependencyHandler):
    """
    Dependency handler to handle dependent files for a given Python requirement.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    def __init__(self, dependency_list: Any, logger: Optional[Logger] = None) -> None:
        """
        Constructor __init__(PyDependencyHandler)

        :param logger: Logger to use

        :since: 0.2.0
        """

        AbstractDependencyHandler.__init__(self, dependency_list, logger)

        self._py_permanent_list = PyPermanentList()

    def scan_for_requirement_uri(self, requirement: str) -> None:
        """
        Scans for dependent files for a given requirement URI.

        :param requirement: Requirement to handle

        :since: 0.2.0
        """

        requirement_data = urlsplit(requirement)
        py_file_path = Path(requirement_data.path[1:])

        if py_file_path.suffix.lower() != ".py":
            return None

        self._logger.info(f"Scanning py:///{py_file_path} for dependencies")

        py_list = self._py_permanent_list.detect(py_file_path)

        for py_file in py_list:
            if Path(py_file).suffix.lower() == ".py":
                self._dependency_list.add(py_file)
            else:
                self._dependency_list.detect(py_file)
