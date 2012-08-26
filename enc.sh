#!/bin/sh

if [ -r /etc/puppet/node.yaml ]; then
  /bin/cat /etc/puppet/node.yaml
else
  cat <<EOF
--- 
classes: {}
parameters {}
# /etc/puppet/node.yaml not found or not readable
EOF
fi
