# -*- coding: utf-8 -*-

"""
Dependency handler for apt-tree:/// of unbase OCI
"""

from debian import deb822
from logging import Logger
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qs, urlsplit

from .apt_dependency_handler import AptDependencyHandler
from .dependency_list import DependencyList
from ..constants import DPKG_FILES_IGNORED


class AptTreeDependencyHandler(AptDependencyHandler):
    """
    Dependency handler to handle installed directories and files of an APT
    package and all dependencies.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    def __init__(
        self, dependency_list: DependencyList, logger: Optional[Logger] = None
    ) -> None:
        """
        dpkg_package = self._get_dpkg_package(package_name)
        self._packages_scanned.append(package_name)

        Constructor __init__(AptTreeDependencyHandler)

        :param logger: Logger to use

        :since: 0.2.0
        """

        AptDependencyHandler.__init__(self, dependency_list, logger)

        self._packages_scanned: List[str] = []

    def scan_for_requirement_uri(self, requirement: str) -> None:
        """
        Scans for dependent files for a given requirement URI.

        :param requirement: Requirement to handle

        :since: 0.2.0
        """

        requirement_data = urlsplit(requirement)
        package_name = requirement_data.path[1:]

        if package_name in self._packages_scanned:
            return None

        requirement_query_data = parse_qs(requirement_data.query)

        is_dependency_scan_skipped = (
            "skip-scan" in requirement_query_data
            and requirement_query_data["skip-scan"][0] == "1"
        )

        self._logger.info(
            f"Scanning apt-tree:///{package_name} for dependencies (skip-scan={is_dependency_scan_skipped})"
        )

        dpkg_package = self._get_dpkg_package(package_name)
        self._packages_scanned.append(package_name)

        list_path = self._get_package_list_path(dpkg_package)

        with list_path.open("r") as list_fp:
            for line in list_fp:
                line = line.strip()

                if line in DPKG_FILES_IGNORED:
                    continue

                if Path(line).is_dir() or is_dependency_scan_skipped:
                    self._dependency_list.add(line)
                else:
                    try:
                        self._dependency_list.detect(line)
                    except Exception as exc:
                        self._logger.warn(
                            f"Issue with Debian package '{package_name}': {exc}"
                        )

        package_relations = dpkg_package.get("Depends")

        if package_relations:
            skip_scan_value = "1" if is_dependency_scan_skipped else ""

            for package_dependencies in deb822.PkgRelation.parse_relations(
                package_relations
            ):
                for package_dependency in package_dependencies:
                    if package_dependency in self._packages_scanned:
                        continue

                    try:
                        self.scan_for_requirement_uri(
                            f"apt-tree:///{package_dependency.get('name')}?skip-scan={skip_scan_value}"
                        )
                    except Exception as exc:
                        self._logger.warn(
                            f"Ignoring Debian package '{package_dependency.get('name')}': {exc}"
                        )
