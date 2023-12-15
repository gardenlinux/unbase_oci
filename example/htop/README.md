# unbase_oci: Guided Example (htop)

This guide demonstrates the utilization of the `unbase_oci` tool to construct a *bare* container image for the `htop` utility program.

Creating a container image to run htop is a straightforward process, achieved with the following `Containerfile`:

```Containerfile
FROM debian
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y htop
CMD [ "htop" ]
```

Executing this through `podman build --tag htop .` yields an image sized at 165MB. Now, let's explore the utilization of `unbase_oci` to streamline this image. We'll employ two methods to highlight their distinctions:
1. Employing dpkg dependencies
2. Leveraging shared library dependencies

## 1. Employing dpkg dependencies

In this approach, we'll exploit the dpkg dependencies of the htop package to determine the essential files for the slimmed-down container image. The `unbase_oci` tool significantly facilitates this process.

Initially, we need to export the container images as oci archives for `unbase_oci` usage:

```shell
podman save --format oci-archive debian > debian.oci
podman save --format oci-archive htop > htop.oci
```

Subsequently, we can initiate the `unbase_oci` tool:

```shell
./unbase_oci --dpkg-dependencies debian.oci htop.oci htop_bare.oci
```

This operation generates a fresh oci archive, named htop_bare.oci, encompassing only the requisite components from htop.oci. The debian base layer is minimized as much as possible. To validate the container image, load it into podman:

```shell
podman load < htop_bare.oci
```

This step provides the sha256 hash sum of the imported image, enabling its tagging with `podman tag IMAGE_HASH htop:bare`. However, executing the image using `podman run --rm -it --pid host htop:bare` results in an error:

```
Error opening terminal: xterm.
```

This arises due to `htop` relying on information in `/etc/terminfo`, which is provided by the `ncurses-base` package. Notably, the `htop` debian package does not explicitly state this dependency, as `ncurses-base` is regarded as an *essential* debian package, and its presence is inherently assumed.

To rectify this, create a file named `dpkg_include` containing the following content:

```
ncurses-base
```

Subsequently, re-run `unbase_oci`, this time incorporating the `--dpkg-include` flag:

```shell
./unbase_oci --dpkg-dependencies --dpkg-include dpkg_include debian.oci htop.oci htop_bare.oci
```

Now, proceed to reload and tag the image:

```shell
podman load < htop_bare.oci
podman tag IMAGE_HASH htop:bare
```

(Ensure the new hash output from `podman load` is employed, replacing the previous one.)

Upon executing `podman run --rm -it --pid host htop:bare`, `htop` functions seamlessly.

To gauge the impact of the container slimming process, refer to `podman image list htop`. The output will resemble the following:

```
REPOSITORY      TAG         IMAGE ID      SIZE
localhost/htop  bare        1fa393aa45c2  45.4 MB
localhost/htop  latest      5c62748f7b15  165 MB
```

Evidently, the container image's size has been substantially reduced (by 71%).

## 2. Utilizing shared library dependencies

In this alternative approach, we solely consider dynamic library dependencies, omitting the reliance on dpkg or other package manager details. Once more, the `unbase_oci` tool streamlines much of the process, though manual fine-tuning is still necessary.

If not done previously, export the debian and htop images as oci archives:

```shell
podman save --format oci-archive debian > debian.oci
podman save --format oci-archive htop > htop.oci
```

Directly running `unbase_oci` in dynamic library dependency mode would result in the same terminfo omission as before. This arises because runtime dependencies, such as config files in `/etc`, cannot be automatically detected; only link time dependencies can.

To circumvent this limitation, create a file named `include` containing the subsequent content:

```
etc/terminfo/.*
usr/lib/terminfo/.*
usr/share/terminfo/.*
```

The file specifies regex patterns; paths matching any of these patterns will be retained in the final image.

Proceed with the following command:

```shell
./unbase_oci --include include --ldd-dependencies debian.oci htop.oci htop_bare.oci
```

Once more, load and tag the image:

```shell
podman load < htop_bare.oci
podman tag IMAGE_HASH htop:bare
```

This action similarly yields a functional htop container image.

A review of `podman image list htop` shows an even more substantial image size reduction, now by 85%:

```
REPOSITORY      TAG         IMAGE ID      SIZE
localhost/htop  bare        9efb3ca1d364  23.2 MB
localhost/htop  latest      5c62748f7b15  165 MB
```

## Further Reducing Image Size

Thus far, `unbase_oci` has incorporated all files from the htop image that were new or altered relative to the debian base. However, an inspection of the image rootfs contents (e.g., using the `--print-tree` flag when invoking `unbase_oci`) reveals the presence of unnecessary elements, primarily related to apt and items in `/usr/share`.

To eliminate these extraneous files, despite their identification as new, a new file named `exclude` can be established with the ensuing contents:

```
usr/share/(applications|doc|icons|man|pixmaps)
var/cache
var/lib/apt
var/log
```

Subsequently, execute `unbase_oci` once more:

```shell
./unbase_oci --include include --exclude exclude --ldd-dependencies debian.oci htop.oci htop_bare.oci
```

This ultimate optimization step culminates in an impressive image size reduction of 97%.
