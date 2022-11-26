#!/bin/bash
if [[ -z "${CXX_WRAP}" ]]; then
  >&2 echo "Error: CXX_WRAP environment variable not set!"
  exit 255
else
  exec ${CXX_WRAP} "${@}"
fi
