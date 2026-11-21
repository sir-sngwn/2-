#!/usr/bin/env bash
#
#  focus_toggle.3s.sh
#  방중 프로젝트 - SwiftBar 메뉴바 토글 스크립트
#

DIR="$HOME/focus_project"
PROG="$DIR/focus_monitor"
SCRIPT="/Users/kimseongwonmac/focus_project/SwiftBarPlugins/focus_toggle.3s.sh"

# 1. 차단 목록 관리기(Manager) 터미널 실행
if [ "$1" = "manager" ]; then
    cd "$DIR"
    ./focus_manager
    exit 0
fi

# 2. 집중 모드 켜기/끄기 토글
if [ "$1" = "toggle" ]; then
    if pgrep -f "focus_monitor" > /dev/null; then
        pkill -9 -f "focus_monitor"
        pkill -9 -f "user-data-dir=/tmp/focus_pet" > /dev/null 2>&1
    else
        nohup "$PROG" "$DIR" > /dev/null 2>&1 &
    fi
    exit 0
fi

# 3. 메뉴바 상태 표시
if pgrep -f "focus_monitor" > /dev/null; then
    echo "🟢 집중모드 ON"
    echo "---"
    echo "집중모드 끄기 | bash=$SCRIPT param1=toggle terminal=false refresh=true"
    echo "차단 목록 관리기(Manager) 열기 | bash=$SCRIPT param1=manager terminal=true"
else
    echo "⚪ 집중모드 OFF"
    echo "---"
    echo "집중모드 켜기 | bash=$SCRIPT param1=toggle terminal=false refresh=true"
    echo "차단 목록 관리기(Manager) 열기 | bash=$SCRIPT param1=manager terminal=true"
fi
