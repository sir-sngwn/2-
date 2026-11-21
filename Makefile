# ==============================================================================
# 방중 프로젝트 (Focus Blocker & SwiftBar Integration) Makefile
# ==============================================================================

CXX = clang++
CXXFLAGS = -std=c++11 -O2 -Wall
SRC_DIR = src

MANAGER_BIN = $(SRC_DIR)/focus_manager
MONITOR_BIN = $(SRC_DIR)/focus_monitor
PLUGIN_SCRIPT = SwiftBarPlugins/focus_toggle.3s.sh

.PHONY: all setup clean run-manager run-monitor stop-monitor status help

all: $(MANAGER_BIN) $(MONITOR_BIN)
	@echo "✅ [빌드 완료] focus_manager 및 focus_monitor가 성공적으로 컴파일되었습니다."

# 처음 설치 시 원클릭 환경 구성
setup: all
	@echo "⚙️  초기 환경 설정을 진행합니다..."
	@chmod +x $(PLUGIN_SCRIPT)
	@ln -sfn "$(CURDIR)/$(SRC_DIR)" "$$HOME/focus_project"
	@defaults write com.ameba.SwiftBar PluginDirectory "$(CURDIR)/SwiftBarPlugins" 2>/dev/null || true
	@open -g "swiftbar://refreshallplugins" 2>/dev/null || true
	@echo "🎉 [설치 및 설정 완료] 모든 준비가 끝났습니다!"
	@echo "   - 상단 메뉴바의 SwiftBar 아이콘(⚪ 집중모드 OFF)을 확인해보세요."
	@echo "   - 또는 make run-manager 명령어로 차단 목록을 관리할 수 있습니다."

$(MANAGER_BIN): $(SRC_DIR)/manager.cpp
	@echo "🔨 컴파일 중: $(MANAGER_BIN)..."
	$(CXX) $(CXXFLAGS) -o $@ $<

$(MONITOR_BIN): $(SRC_DIR)/monitor.cpp
	@echo "🔨 컴파일 중: $(MONITOR_BIN)..."
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	@echo "🧹 실행 파일 정리 중..."
	rm -f $(MANAGER_BIN) $(MONITOR_BIN)
	@echo "✅ 정리 완료."

run-manager: $(MANAGER_BIN)
	@echo "🚀 차단 목록 관리기(Manager)를 실행합니다..."
	cd "$(SRC_DIR)" && ./focus_manager

run-monitor: $(MONITOR_BIN)
	@echo "🚀 백그라운드 집중 모니터(Monitor)를 시작합니다..."
	nohup "$(CURDIR)/$(MONITOR_BIN)" "$(CURDIR)/$(SRC_DIR)" > /dev/null 2>&1 &
	@echo "🟢 집중모드가 시작되었습니다."

stop-monitor:
	@echo "🛑 집중모드 프로세스를 종료합니다..."
	@pkill -f "focus_monitor" 2>/dev/null || echo "실행 중인 모니터 프로세스가 없습니다."
	@echo "⚪ 집중모드가 종료되었습니다."

status:
	@if pgrep -f "focus_monitor" > /dev/null; then echo "🟢 집중모드 [ON] 실행 중"; else echo "⚪ 집중모드 [OFF] 중지됨"; fi

help:
	@echo "방중 프로젝트 사용 가능한 명령어:"
	@echo "  make setup        - 처음 다운로드 후 원클릭 빌드 + SwiftBar 연동 설정"
	@echo "  make              - C++ 실행 파일 2개 (manager, monitor) 컴파일"
	@echo "  make run-manager  - 웹사이트/프로세스 차단 목록 편집기 실행"
	@echo "  make run-monitor  - 백그라운드 집중 모니터 시작"
	@echo "  make stop-monitor - 백그라운드 집중 모니터 종료"
	@echo "  make status       - 현재 집중 모드 ON/OFF 상태 확인"
	@echo "  make clean        - 컴파일된 실행 파일 삭제"
