#!/bin/bash

for arg in "$@";
do
    if ( echo "${arg}" | grep -q '^DESTDIR=' );
    then
        export "${arg}"
    fi
done

if [ -z "${DESTDIR}" ];
then
    DESTDIR=""
else
    if [ "${DESTDIR}" != "/" ];
    then
        DESTDIR="$(echo "${DESTDIR}" | sed 's|[/][/]*$||g')"
        DESTDIR="$(echo "${DESTDIR}" | sed 's|//|/|g')"
    else
        DESTDIR=''
    fi
fi

SYSTEMDDIR="${DESTDIR}/usr/lib/systemd/system"
SYSTEMDDIR="$(echo "${SYSTEMDDIR}" | sed 's|//|/|g')"

mkdir -p "${SYSTEMDDIR}"

install -m 644 'usrsvcd@.service' "${SYSTEMDDIR}/"
RET=$?
if [ $RET -ne 0 ];
then
    echo;
    echo;
    echo "WARNING: Install returned non-zero. Check for errors above"'!';
    exit ${RET}
fi
