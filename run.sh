#!/usr/bin/env bash

# 루트 디렉터리에서 실행 시 desktop-pet/run.sh로 자동 위임
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/desktop-pet/run.sh" "$@"
