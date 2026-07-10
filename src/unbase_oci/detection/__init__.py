# -*- coding: utf-8 -*-

"""
Detection module
"""

from .abstract_dependency_handler import AbstractDependencyHandler
from .apt_dependency_handler import AptDependencyHandler
from .apt_tree_dependency_handler import AptTreeDependencyHandler
from .file_dependency_handler import FileDependencyHandler
from .py_dependency_handler import PyDependencyHandler
from .dependency_list import DependencyList
from .magic import Magic

__all__ = [
    "AbstractDependencyHandler",
    "AptDependencyHandler",
    "AptTreeDependencyHandler",
    "FileDependencyHandler",
    "PyDependencyHandler",
    "DependencyList",
    "Magic",
]
