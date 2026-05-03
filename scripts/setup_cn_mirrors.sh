#!/usr/bin/env bash
set -euo pipefail

python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

if command -v npm >/dev/null 2>&1; then
  npm config set registry https://registry.npmmirror.com
fi

printf '%s\n' 'China mainland package mirrors configured.'
