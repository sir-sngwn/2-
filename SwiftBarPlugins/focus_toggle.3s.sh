#!/usr/bin/env bash
#
#  focus_toggle.3s.sh
#  방중 프로젝트 - SwiftBar 메뉴바 토글 스크립트
#

DIR="$HOME/focus_project"
PROG="$DIR/focus_monitor"
SCRIPT="/Users/kimseongwonmac/focus_project/SwiftBarPlugins/focus_toggle.3s.sh"

if [ "$1" = "manager" ]; then
    cd "$DIR"
    ./focus_manager
    exit 0
fi

if [ "$1" = "toggle" ]; then
    if pgrep -f "focus_monitor" > /dev/null; then
        pkill -9 -f "focus_monitor"
        pkill -9 -f "user-data-dir=/tmp/focus_pet" > /dev/null 2>&1
    else
        nohup "$PROG" "$DIR" > /dev/null 2>&1 &
    fi
    exit 0
fi

if pgrep -f "focus_monitor" > /dev/null; then
    echo "🟢 FOCUS MODE ON"
    echo "---"
    echo "TURN OFF | bash=$SCRIPT param1=toggle terminal=false refresh=true"
    echo "MANAGER | bash=$SCRIPT param1=manager terminal=true"
else
    echo "⚪ FOCUS MODE OFF"
    echo "---"
    echo "TURN ON | bash=$SCRIPT param1=toggle terminal=false refresh=true"
    echo "MANAGER | bash=$SCRIPT param1=manager terminal=true"
fi
