# -*- coding: utf-8 -*-

"""
Dependency handler for apt:/// of unbase OCI
"""

from debian import deb822
from pathlib import Path
from urllib.parse import urlsplit

from .abstract_dependency_handler import AbstractDependencyHandler
from ..constants import DPKG_FILES_IGNORED, DPKG_MULTI_ARCH_VALUES, DPKG_VAR_PATH


class AptDependencyHandler(AbstractDependencyHandler):
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

    def _get_dpkg_package(self, package_name: str) -> deb822.Deb822:
        """
        Returns the Debian package definition for the package name given.

        :param package: Debian package definition

        :return: (object) Debian package list file path
        :since:  0.2.0
        """

        dpkg_status_path = DPKG_VAR_PATH.joinpath("status")

        if not dpkg_status_path.exists():
            raise RuntimeError("Debian dpkg status is missing")

        dpkg_package = None

        with dpkg_status_path.open("r") as dpkg_status_fp:
            for package in deb822.Packages.iter_paragraphs(dpkg_status_fp):
                if package.get("Package") == package_name:
                    dpkg_package = package
                    break

        if dpkg_package is None:
            raise RuntimeError(f"Debian package '{package_name}' not in dpkg status")

        return dpkg_package

    def _get_package_list_path(self, package: deb822.Deb822) -> Path:
        """
        Returns the path to the package list file for the Debian package definition
        given.

        :param package: Debian package definition

        :return: (object) Debian package list file path
        :since:  0.2.0
        """

        architecture = package.get("Architecture", "any")
        multi_arch = package.get("Multi-Arch")
        package_name = package.get("Package")

        list_path = (
            DPKG_VAR_PATH.joinpath("info", f"{package_name}:{architecture}.list")
            if multi_arch in DPKG_MULTI_ARCH_VALUES
            else None
        )

        if list_path is None or not list_path.exists():
            list_path = DPKG_VAR_PATH.joinpath("info", f"{package_name}.list")

        if not list_path.exists():
            raise RuntimeError(
                f"Failed to find Debian files list based on package '{package_name}:{architecture}' ({multi_arch})"
            )

        return list_path

    def scan_for_requirement_uri(self, requirement: str) -> None:
        """
        Scans for dependent files for a given requirement URI.

        :param requirement: Requirement to handle

        :since: 0.2.0
        """

        requirement_data = urlsplit(requirement)
        package_name = requirement_data.path[1:]

        self._logger.info(f"Scanning apt:///{package_name} for dependencies")

        dpkg_package = self._get_dpkg_package(package_name)
        list_path = self._get_package_list_path(dpkg_package)

        with list_path.open("r") as list_fp:
            for line in list_fp:
                line = line.strip()

                if line in DPKG_FILES_IGNORED:
                    continue

                if Path(line).is_dir():
                    self._dependency_list.add(line)
                else:
                    try:
                        self._dependency_list.detect(line)
                    except Exception as exc:
                        self._logger.warn(
                            f"Issue with Debian package '{package_name}': {exc}"
                        )
