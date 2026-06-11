# -*- coding: utf-8 -*-

from pathlib import Path

DEPENDENCY_LIST_MAX_CACHE_ENTRIES = 4194304

DEPENDENCY_LIST_SUPPORTED_MIME_MAGICS = (
    "application/x-executable",
    "application/x-pie-executable",
    "application/x-mach-binary",
    "text/x-script.python",
)

DPKG_FILES_IGNORED = ("", "/", ".", "/.")
DPKG_MULTI_ARCH_VALUES = ("same", "foreign", "allowed")
DPKG_VAR_PATH = Path("/var/lib/dpkg")

SCHEMES_FILE_JSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"scheme": {"type": "string"}, "handler": {"type": "string"}},
    },
}
"""
JSON schema to validate handler schemes files
"""
