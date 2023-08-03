FROM sarasmiseth/prosody:latest

USER root
RUN apt-get update && \
        apt-get -y install certbot

RUN download-prosody-modules.bash \
 && docker-prosody-module-install.bash \
        cloud_notify \
        cloud_notify_extensions \
        privilege \
 && rm -rf "/usr/src/prosody-modules"

USER prosody
