FROM debian
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y bsdextrautils jq oci-image-tool patchelf tree
COPY src /opt/unbase_oci
ENTRYPOINT [ "/opt/unbase_oci/entrypoint" ]
