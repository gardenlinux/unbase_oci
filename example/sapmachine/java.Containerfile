FROM debian
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y default-jdk
