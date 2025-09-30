#!/bin/bash

podman pull ghcr.io/gardenlinux/gardenlinux:1592.14
podman build -t huge-image .
./unbase_oci --ldd-dependencies podman:ghcr.io/gardenlinux/gardenlinux:1592.14 podman:huge-image:latest podman:huge-image:bare
