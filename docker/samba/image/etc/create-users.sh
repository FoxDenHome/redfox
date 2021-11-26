#!/bin/sh
set -e

SHELL=/bin/zsh

mksysuser() {
    adduser -s /sbin/nologin -D -u "$2" "$1"
}

mknasuser() {
    adduser -s "$SHELL" -D -u "$2" "$1"
    adduser "$1" share
}

mksysuser smbauth  401
mksysuser smbguest 403
mksysuser share    1000
mknasuser doridian 1001
mknasuser wizzy    1002