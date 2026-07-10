# -*- coding: utf-8 -*-

"""
Dependency detector based on execution of unbase OCI inside container
"""

from binascii import hexlify
from fnmatch import filter as fnfilter
from importlib.resources import read_text as importlib_read_text
from pathlib import Path
from shlex import quote
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional
import json
import os

from podman_context import (
    Podman,
    PodmanContext,
    PodmanObjectContext,
    PODMAN_FS_CHANGE_ADDED,
    PODMAN_FS_CHANGE_MODIFIED,
)

from .requirements_scheme_mixin import RequirementsSchemeMixin


class UnbaseOCIContainer(PodmanObjectContext, RequirementsSchemeMixin):
    """
    Executes the unbase OCI container requests using Podman.

    :author:     Garden Linux Maintainers
    :copyright:  Copyright 2026 SAP SE
    :package:    unbase_oci
    :subpackage: detection
    :since:      0.2.0
    :license:    https://www.apache.org/licenses/LICENSE-2.0
                 Apache License, Version 2.0
    """

    def __init__(
        self,
        oci_id: str,
        /,
        podman: Optional[PodmanContext] = None,
    ) -> None:
        """
        Constructor __init__(UnbaseOCIContainer)
        @TODO: Fix me

        :since: 0.2.0
        """

        PodmanObjectContext.__init__(self)
        RequirementsSchemeMixin.__init__(self)

        self._scan_containerfile_content: Optional[str] = None
        self._scan_entrypoint_content: Optional[str] = None
        self._oci_id = oci_id
        self._podman = podman

    @property
    def scan_containerfile_content(self) -> str:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if self._scan_containerfile_content is None:
            self._scan_containerfile_content = importlib_read_text(
                "unbase_oci", "dependency_detection.partial.Containerfile"
            )

        return self._scan_containerfile_content

    @scan_containerfile_content.setter
    def scan_containerfile_content(self, value: str) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        self._scan_containerfile_content = value

    @property
    def scan_entrypoint_content(self) -> str:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if self._scan_entrypoint_content is None:
            self._scan_entrypoint_content = importlib_read_text(
                "unbase_oci", "dependency_detection_entrypoint.sh"
            )

        return self._scan_entrypoint_content

    @scan_entrypoint_content.setter
    def scan_entrypoint_content(self, value: str) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        self._scan_entrypoint_content = value

    @PodmanObjectContext.wrap_for_self_podman
    def compare_with_base_oci(
        self, base_oci_path: str, exclude_globs: List[str], /, podman: PodmanContext
    ) -> List[str]:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not Path(base_oci_path).exists():
            raise RuntimeError(f"No such file or directory: {base_oci_path}")

        base_oci_id = None
        podman_api = Podman()

        try:
            base_oci_id = podman_api.load_oci_archive(base_oci_path, podman=podman)

            changes_list = []

            podman_image = podman_api.get_image(self._oci_id, podman=podman)

            podman_changes = podman_image.get_filesystem_changes(
                parent_layer_image_id=base_oci_id, podman=podman
            )

            podman_changes_list = (
                podman_changes[PODMAN_FS_CHANGE_ADDED]
                + podman_changes[PODMAN_FS_CHANGE_MODIFIED]
            )

            for source_file in podman_changes_list:
                if source_file not in changes_list and not Path(source_file).is_dir():
                    changes_list.append(source_file)

            excluded_changes_list = []

            for exclude_glob in exclude_globs:
                excluded_changes_list += fnfilter(changes_list, exclude_glob)

            # Only consider files for dependency scans
            return [
                f"file:///{value}"
                for value in changes_list
                if value not in excluded_changes_list
            ]
        finally:
            if base_oci_id is not None:
                podman.images.remove(base_oci_id)

    @PodmanObjectContext.wrap_for_self_podman
    def export_into_oci_archive(
        self,
        sources: Dict[str, List[str]],
        target_oci: str | os.PathLike[str],
        /,
        podman: PodmanContext,
        new_entrypoint: Optional[str] = None,
        new_workdir: Optional[str] = None,
        precopy_containerfile: Optional[str | os.PathLike[str]] = None,
    ) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(target_oci, Path):
            target_oci = Path(target_oci)

        if target_oci.exists():
            raise RuntimeError(f"Target file '{target_oci}' already exists")

        if not os.access(target_oci.parent, os.W_OK):
            raise RuntimeError(
                f"Target directory '{target_oci.parent}' is not writable"
            )

        if precopy_containerfile:
            if not isinstance(precopy_containerfile, Path):
                precopy_containerfile = Path(precopy_containerfile)

            if not precopy_containerfile.exists():
                raise RuntimeError(
                    f"No such file or directory: {precopy_containerfile}"
                )
        else:
            precopy_containerfile = None

        with TemporaryDirectory() as tmpdir:
            export_container = None
            export_image_id = None
            exported_image = None

            try:
                self._logger.info(
                    f"Exporting {len(sources['dependencies'])} files and {len(sources['symlink_dependencies'])} symlinks"
                )

                copy_files_list = []

                for copy_file in sources["dependencies"]:
                    copy_files_list.append('"' + quote(copy_file) + '"')

                if len(copy_files_list) > 0:
                    copy_files = ", ".join(copy_files_list)
                else:
                    self._logger.warn(
                        "Source dependencies are empty, copying everything"
                    )

                    copy_files = '"/"'

                copy_symlink_lines_list = []

                for copy_file in sources["symlink_dependencies"]:
                    copy_file_path = Path(copy_file)

                    copy_symlink_lines_list.append(
                        f"RUN mkdir -p /.precopyroot{copy_file_path.parent} && cp -a {copy_file} /.precopyroot{copy_file_path.parent}"
                    )

                copy_symlink_lines = "\n".join(copy_symlink_lines_list)
                precopy_containerfile_content = ""

                if precopy_containerfile is not None:
                    precopy_containerfile_content = precopy_containerfile.read_text()

                containerfile = Path(tmpdir, "ContainerFile")

                containerfile_content = f"""
FROM {self._oci_id} AS source

RUN mkdir /.precopyroot

{precopy_containerfile_content}
{copy_symlink_lines}

FROM scratch AS stripped

COPY --from=source --parents [ {copy_files}, "/" ]
COPY --from=source /.precopyroot/ /
""".strip()

                if new_workdir:
                    containerfile_content += f"\n\nWORKDIR {quote(new_workdir)}"

                if new_entrypoint:
                    containerfile_content += f"\n\nENTRYPOINT {new_entrypoint}"

                containerfile.write_text(containerfile_content)

                exported_image, log = podman.images.build(
                    path=tmpdir,
                    dockerfile=containerfile,
                    layers=False,
                )

                for line in log:
                    self._logger.debug(json.loads(line)["stream"].strip())

                self._logger.debug(f"Writing OCI archive: {target_oci}")

                with target_oci.open("wb") as fp:
                    for chunk in exported_image.save():
                        fp.write(chunk)
            finally:
                if export_container is not None:
                    export_container.remove()
                if export_image_id is not None:
                    podman.images.remove(export_image_id)
                if exported_image is not None:
                    podman.images.remove(exported_image)

    def load_scan_containerfile_file(
        self, containerfile_path: str | os.PathLike[str]
    ) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(containerfile_path, Path):
            containerfile_path = Path(containerfile_path)

        if not containerfile_path.exists():
            raise RuntimeError(f"No such file or directory: {containerfile_path}")

        self.scan_containerfile_content = containerfile_path.read_text()

    def load_scan_entrypoint_file(
        self, entrypoint_path: str | os.PathLike[str]
    ) -> None:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        if not isinstance(entrypoint_path, Path):
            entrypoint_path = Path(entrypoint_path)

        if not entrypoint_path.exists():
            raise RuntimeError(f"No such file or directory: {entrypoint_path}")

        self.scan_entrypoint_content = entrypoint_path.read_text()

    @PodmanObjectContext.wrap_for_self_podman
    def scan(
        self,
        requirements_list: List[str],
        exclude_globs: List[str],
        /,
        podman: PodmanContext,
    ) -> Dict[str, List[str]]:
        """
        @TODO: Fix me

        :param args: Arguments parsed

        :since: 0.2.0
        """

        with TemporaryDirectory() as tmpdir:
            detector_container = None
            detector_image_id = None

            try:
                self._logger.info(
                    f"Detecting dependencies for {len(requirements_list)} requirements"
                )

                entrypoint_file = Path(tmpdir, "entrypoint.sh")

                if self.scan_entrypoint_content is not None:
                    entrypoint_file.write_text(self.scan_entrypoint_content)

                randomized_suffix = hexlify(os.urandom(3)).decode("utf-8")
                exclude_globs.append(f"/opt/unbase_oci_{randomized_suffix}/*")

                unbase_inplace_file = Path(tmpdir, "unbase_inplace.json")

                unbase_inplace_file.write_text(
                    json.dumps(
                        {
                            "requirements": requirements_list,
                            "exclude_globs": exclude_globs,
                            "dependencies": [],
                            "symlink_dependencies": [],
                        }
                    )
                )

                schemes: List[Dict[str, str]] = []

                for (
                    requirement_scheme,
                    requirement_handler,
                ) in self._external_requirement_handlers.items():
                    schemes.append(
                        {
                            "scheme": requirement_scheme,
                            "handler": f"{requirement_handler.__module__}.{requirement_handler.__name__}",
                        }
                    )

                schemes_file = Path(tmpdir, "unbase_schemes.json")
                schemes_file.write_text(json.dumps(schemes))

                containerfile = Path(tmpdir, "ContainerFile")

                containerfile.write_text(
                    f"""
FROM {self._oci_id}

ARG RANDOMIZED_SUFFIX={randomized_suffix}
ENV UNBASE_OCI_RANDOMIZED_SUFFIX=$RANDOMIZED_SUFFIX

WORKDIR /opt/unbase_oci_${{RANDOMIZED_SUFFIX}}/
{self.scan_containerfile_content}

COPY --chmod=0755 {entrypoint_file.name} /opt/unbase_oci_${{RANDOMIZED_SUFFIX}}/
COPY {schemes_file.name} /opt/unbase_oci_${{RANDOMIZED_SUFFIX}}/

ENTRYPOINT ["./entrypoint.sh"]
                """.strip()
                )

                image, log = podman.images.build(
                    path=tmpdir, dockerfile=containerfile, layers=False
                )

                for line in log:
                    self._logger.debug(json.loads(line)["stream"].strip())

                detector_image_id = image.id

                detector_container = podman.containers.create(
                    detector_image_id,
                    detach=False,
                    mounts=[
                        {
                            "type": "bind",
                            "source": str(unbase_inplace_file),
                            "target": f"/opt/unbase_oci_{randomized_suffix}/unbase_inplace.json",
                        }
                    ],
                )

                detector_container.start()
                detector_container.wait(condition="exited")

                for log in detector_container.logs():
                    self._logger.debug(log.decode("utf-8").strip())

                return json.loads(unbase_inplace_file.read_text())  # type: ignore[no-any-return]
            finally:
                if detector_container is not None:
                    detector_container.remove()
                if detector_image_id is not None:
                    podman.images.remove(detector_image_id)
