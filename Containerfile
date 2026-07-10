FROM ghcr.io/gardenlinux/gardenlinux:latest

# Keep in sync with ./build
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y podman python3-pip conmon crun netavark nftables

COPY src /opt/unbase_oci
WORKDIR /opt/unbase_oci

COPY requirements.txt /opt/unbase_oci
RUN pip install --break-system-packages -r requirements.txt
RUN touch /var/tmp/.keep

ENTRYPOINT [ "python3", "-m", "unbase_oci" ]
