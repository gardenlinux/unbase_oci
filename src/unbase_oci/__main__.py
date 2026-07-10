# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import os

from podman_context import (
    Podman,
    PodmanContext,
)

from .dependency_scanner import DependencyScanner
from .unbase_oci_container import UnbaseOCIContainer


def get_parser() -> argparse.ArgumentParser:
    """
    Get the argument parser for unbase OCI.
    Used for documentation generation.

    :return: ArgumentParser instance
    :since: 0.2.0
    """

    parser = argparse.ArgumentParser(
        prog="unbase_oci", description="Streamline OCI container images."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scans a file system and additional sources based on a given list of required entries.",
    )

    scan_parser.add_argument(
        "--unbase-inplace-file",
        required=True,
        help="File with required entries used in-place to add a list of unbase OCI detected dependencies to",
    )

    scan_parser.add_argument(
        "--python-env-self-dependencies",
        type=bool,
        default=False,
        help="Use the Python environment expected to satisfy Python file package imports",
    )

    scan_parser.add_argument(
        "--requirements-scheme",
        action="append",
        default=[],
        help="List of schemes for URIs used in required entries",
    )

    scan_parser.add_argument(
        "--requirements-schemes-file",
        default="",
        help="JSON file path and name containing a list of schemes for URIs used in required entries",
    )

    strip_parser = subparsers.add_parser(
        "strip", help="Strips unused dependencies from an OCI container."
    )

    strip_parser.add_argument(
        "--base-oci",
        default="base_layer.oci",
        help="OCI base container used for comparison.",
    )

    strip_parser.add_argument(
        "--source-oci",
        default="source_container.oci",
        help="OCI source container including all required changes.",
    )

    strip_parser.add_argument(
        "--target-oci",
        required=True,
        help="File path and name to the stripped OCI container.",
    )

    strip_parser.add_argument(
        "--containerfile",
        default="",
        help="File path and name to a script calling unbase OCI scanning.",
    )

    strip_parser.add_argument(
        "--entrypoint-file",
        default="",
        help="File path and name to a script calling unbase OCI scanning.",
    )

    strip_parser.add_argument(
        "--new-entrypoint",
        default="",
        help="Sets a new entrypoint for the generated OCI target.",
    )

    strip_parser.add_argument(
        "--new-workdir",
        default="",
        help="Sets a new workdir for the generated OCI target.",
    )

    strip_parser.add_argument(
        "--scan-exclude",
        action="append",
        default=[],
        help="Exclude files and directories from dependency scanning. May result in broken symlinks with certain external dependency handlers.",
    )

    strip_parser.add_argument(
        "--source-exclude",
        action="append",
        default=[],
        help="Exclude files and directories from OCI source layer scanning. Dependency detection will resolve files within excluded entries.",
    )

    strip_parser.add_argument(
        "--precopy-containerfile",
        default="",
        help="File path and name to a script called for additional pre-copy preparations for the unbase OCI target.",
    )

    strip_parser.add_argument(
        "--dependency",
        "-d",
        action="append",
        default=[],
        help="Additional directories and files (binaries, libraries) supported by the dependency scanner.",
    )

    strip_parser.add_argument(
        "--dependencies-file",
        default="",
        help="File path and name for a list with one dependency per line supported by the dependency scanner.",
    )

    strip_parser.add_argument(
        "--requirements-scheme",
        action="append",
        default=[],
        help="List of schemes for URIs used in required entries",
    )

    strip_parser.add_argument(
        "--requirements-schemes-file",
        default="",
        help="JSON file path and name containing a list of schemes for URIs used in required entries",
    )

    return parser


def main() -> None:
    """
    Main entrypoint for unbase OCI.

    :since: 0.2.0
    """

    parser = get_parser()
    args = parser.parse_args()

    match args.command:
        case "scan":
            _main_scan(args)
        case "strip":
            _main_strip(args)
        case _:
            parser.print_help()


def _main_scan(
    args: argparse.Namespace,
) -> None:
    """
    Main execution for unbase OCI scanning.

    :param args: Arguments parsed

    :since: 0.2.0
    """

    if not Path(args.unbase_inplace_file).exists():
        raise RuntimeError(f"No such file or directory: {args.unbase_inplace_file}")

    if not os.access(Path(args.unbase_inplace_file).parent, os.W_OK):
        raise RuntimeError(
            f"Failed to validate unbase OCI inplace JSON file '{args.unbase_inplace_file}'"
        )

    dependency_scanner = DependencyScanner(
        args.unbase_inplace_file, args.python_env_self_dependencies
    )

    if args.requirements_schemes_file:
        dependency_scanner.load_schemes_file(args.requirements_schemes_file)

    for scheme in args.requirements_scheme:
        if ":///" not in scheme:
            continue

        dependency_scanner.add_scheme(*scheme.split(":///", 1))

    dependency_scanner.scan()


def _main_strip(
    args: argparse.Namespace,
) -> None:
    """
    Main execution for unbase OCI stripping.

    :param args: Arguments parsed

    :since: 0.2.0
    """

    if not Path(args.base_oci).exists():
        raise RuntimeError(f"No such file or directory: {args.base_oci}")

    if not os.access(Path(args.target_oci).parent, os.W_OK):
        raise RuntimeError(
            f"Failed to validate target OCI container directory for '{args.target_oci}'"
        )

    dependencies_file_path = None

    if args.dependencies_file:
        dependencies_file_path = Path(args.dependencies_file)

        if not dependencies_file_path.exists():
            raise RuntimeError(f"No such file or directory: {args.dependencies_file}")

    with PodmanContext() as podman_context:
        podman_api = Podman()
        detection_oci_id = None
        scan_base_oci = False

        try:
            if args.source_oci and Path(args.source_oci).exists():
                detection_oci_id = podman_api.load_oci_archive(
                    args.source_oci, podman=podman_context
                )

                scan_base_oci = True
            else:
                detection_oci_id = podman_api.load_oci_archive(
                    args.base_oci, podman=podman_context
                )

            container = UnbaseOCIContainer(detection_oci_id, podman=podman_context)

            if args.containerfile:
                container.load_scan_containerfile_file(args.containerfile)

            if args.entrypoint_file:
                container.load_scan_entrypoint_file(args.entrypoint_file)

            if args.requirements_schemes_file:
                container.load_schemes_file(args.requirements_schemes_file)

            for scheme in args.requirements_scheme:
                if ":///" not in scheme:
                    continue

                container.add_scheme(*scheme.split(":///", 1))

            if scan_base_oci:
                requirements_list = container.compare_with_base_oci(
                    args.base_oci, args.source_exclude
                )
            else:
                requirements_list = []

            for dependency in args.dependency:
                if dependency not in requirements_list:
                    requirements_list.append(dependency)

            if dependencies_file_path is not None:
                with dependencies_file_path.open("r") as fp:
                    for dependency in fp:
                        dependency = dependency.strip()

                        if dependency not in requirements_list:
                            requirements_list.append(dependency)

            scanned_sources = container.scan(requirements_list, args.scan_exclude)

            container.export_into_oci_archive(
                scanned_sources,
                args.target_oci,
                new_entrypoint=args.new_entrypoint,
                new_workdir=args.new_workdir,
                precopy_containerfile=args.precopy_containerfile,
            )
        finally:
            if detection_oci_id is not None and podman_context.images.exists(
                detection_oci_id
            ):
                podman_context.images.remove(detection_oci_id)


if __name__ == "__main__":
    main()
