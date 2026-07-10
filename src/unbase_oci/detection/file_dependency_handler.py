# -*- coding: utf-8 -*-

"""
Dependency handler for file:/// of unbase OCI
"""

from pathlib import Path
from urllib.parse import urlsplit

from .abstract_dependency_handler import AbstractDependencyHandler


class FileDependencyHandler(AbstractDependencyHandler):
    """
    Dependency handler to handle the installed directories and files of an APT
    package.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    def scan_for_requirement_uri(self, requirement: str) -> None:
        """
        Scans for dependent files for a given requirement URI.

        :param requirement: Requirement to handle

        :since: 0.2.0
        """

        requirement_data = urlsplit(requirement)
        file_path = requirement_data.path[1:]

        self._logger.info(f"Scanning file:///{file_path} for dependencies")

        if not Path(file_path).is_dir():
            self._dependency_list.detect(file_path)
