# -*- coding: utf-8 -*-

"""
Abstract dependency handler of unbase OCI
"""

from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Any, Optional


class AbstractDependencyHandler(ABC):
    """
    Dependency handlers scan for dependent files for given requirements.

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
        Constructor __init__(AbstractDependencyHandler)

        :param logger: Logger to use

        :since: 0.2.0
        """

        if logger is None or not logger.hasHandlers():
            logger = getLogger("unbase_oci.detection")

        self._dependency_list = dependency_list
        self._logger = logger

    @abstractmethod
    def scan_for_requirement_uri(self, requirement: str) -> None:
        """
        Scans for dependent files for a given requirement URI.

        :param requirement: Requirement to handle

        :since: 0.2.0
        """

        raise NotImplementedError("Method not implemented")
