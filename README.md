# unbase_oci: Streamline OCI Container Images

The **unbase OCI tool** is designed to streamline container images by eliminating unnecessary components inherited from the base container, thereby reducing bloat and enhancing security.
It essentially produces a so called *"distroless"* container image.
Operating on OCI archives, the tool performs a thorough comparison between a base image and a target image.
It identifies additions made to the target image in relation to the base image, as well as the dependencies of these additions.
The tool then strips away extraneous elements, resulting in a minimized target image.

## Requirements

To utilize this tool, you only need a bash shell, along with two standard Unix tools: `realpath` and `touch`.
Additionally, a functional container engine is necessary.
By default, the tool employs `podman` as the container engine, though this can be customized using the `--container-engine` option (see usage section below).

## Installation

Installation is a straightforward process:

1. Download the `unbase_oci` script from the latest GitHub release.
2. Grant executable permissions to the script.

```shell
wget https://github.com/gardenlinux/unbase_oci/releases/download/latest/unbase_oci
chmod +x unbase_oci
```

## Usage

```
./unbase_oci [options] base_image target_image output_image

Options:
  -i, --include INCLUDE_FILE          Specify regex patterns to selectively include files.
                                      Patterns are in grep extended regex format (one per line).
                                      Patterns must match complete file paths, without leading /.
                                      Note: Directory matches do NOT include directory contents.

  -x, --exclude EXCLUDE_FILE          Specify regex patterns to selectively exclude files.
                                      Same format as include file, however a matching directory does also exclude all
                                      its contents.

  --no-default-include                Skip default inclusion of directory or symlink entries for /proc, /sys, /dev,
                                      /bin, /sbin.

  --no-default-exclude                Disable default exclusions of /etc/ld.so.cache and /var/lib/dpkg.

  -d, --dpkg-dependencies             Identify dpkg package dependencies and include required files.

  --dpkg-include DPKG_INCLUDE_FILE    A list of dpkg packages to include.

  -l, --ldd-dependencies              Identify dynamic library dependencies and include necessary files.

  --print-tree                        Display the directory tree of the output rootfs.

  --container-engine ENGINE           Use specified ENGINE as the container engine instead of podman.
```

## Example Usage

For instance, consider building a container on top of a Debian base. Let's assume `debian.oci` represents an exported OCI archive of the Debian base image, while `container.oci` is an exported OCI archive of the target image. To create a *"distroless"* variant of the target container, containing only the dependencies of explicitly installed components on top of Debian (e.g.: libc), execute:

```shell
./unbase_oci --ldd-dependencies debian.oci container.oci container_distroless.oci
```

For a more comprehensive example, please refer to the detailed guide in [example/htop](example/htop/README.md). This will further illustrate the tool's functionality in practice.
