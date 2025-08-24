#!/bin/bash
set -e
if command -v dnf >/dev/null 2>&1; then
  dnf install -y git
else
  yum install -y git
fi
