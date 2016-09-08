#!/bin/bash

install -m 644 'usrsvcd@.service' /usr/lib/systemd/system
systemctl daemon-reload
