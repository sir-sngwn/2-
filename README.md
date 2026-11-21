# 🎯 방중 프로젝트 - 집중 모드 차단 프로그램 (Focus Blocker & SwiftBar)

> 집중을 방해하는 웹사이트와 앱(프로세스)을 주기적으로 감시하여 감지 시 경고 GIF 팝업 창을 띄우고,  
> macOS 상단 메뉴바(SwiftBar)를 통해 클릭 한 번으로 손쉽게 집중 모드를 켜고 끌 수 있는 통합 패키지입니다.

---

## 📌 처음 다운로드 받은 분을 위한 시작 가이드

본 패키지를 처음 내려받은 분은 아래 가이드에 따라 **1분 만에 설치 및 실행**할 수 있습니다.

### 1. 사전 준비 (Prerequisites)
macOS 환경에서 C++ 컴파일러와 메뉴바 연동을 위해 아래 2가지를 확인합니다.

1. **C++ 컴파일러 (Xcode Command Line Tools)**
   터미널에서 컴파일러가 설치되어 있는지 확인합니다:
   ```bash
   clang++ --version
   ```
   만약 설치되어 있지 않다면 아래 명령어로 설치합니다:
   ```bash
   xcode-select --install
   ```

2. **SwiftBar 앱 (메뉴바 연동용)**
   Mac 상단 메뉴바에 🟢/⚪ 토글 버튼을 띄우기 위해 [SwiftBar](https://github.com/swiftbar/SwiftBar) 앱이 필요합니다.
   * **Homebrew를 사용하는 경우:**
     ```bash
     brew install --cask swiftbar
     ```
   * **직접 다운로드하는 경우:**
     [SwiftBar Releases](https://github.com/swiftbar/SwiftBar/releases)에서 `.dmg` 파일을 받아 설치합니다.
   * 설치 후 SwiftBar 앱을 한 번 실행해 둡니다.

---

### 2. 초간단 원클릭 설치 (추천)

프로젝트 폴더 내에서 터미널을 열고 아래 명령어 **한 줄**만 입력하면 모든 빌드와 메뉴바 연동 설정이 자동으로 완료됩니다:

```bash
cd "/Users/kimseongwonmac/Desktop/방중 프로젝트"   # (다운로드 받은 폴더 경로)
make setup
```

#### `make setup`이 자동으로 해주는 작업:
1. `focus_manager` 및 `focus_monitor` C++ 실행 파일 컴파일
2. SwiftBar 플러그인 스크립트 실행 권한(`chmod +x`) 부여
3. SwiftBar 플러그인 폴더를 본 패키지의 `SwiftBarPlugins`로 자동 연결
4. 홈 디렉토리에 편리한 바로가기 링크(`~/focus_project`) 생성
5. SwiftBar 메뉴바 즉시 새로고침

---

### 3. 수동 설치 방법 (직접 세팅을 원하는 경우)

자동 설치 대신 단계별로 직접 설정하고 싶다면 아래 순서로 진행합니다:

1. **실행 파일 컴파일:**
   ```bash
   make
   # 또는 직접 컴파일:
   clang++ -std=c++11 -O2 -o src/focus_manager src/manager.cpp
   clang++ -std=c++11 -O2 -o src/focus_monitor src/monitor.cpp
   ```

2. **플러그인 실행 권한 설정:**
   ```bash
   chmod +x SwiftBarPlugins/focus_toggle.3s.sh
   ```

3. **SwiftBar 플러그인 폴더 연결:**
   * SwiftBar 메뉴바 아이콘 클릭 -> `Preferences...` -> `Change Plugin Folder...`
   * 다운로드받은 본 프로젝트 내부의 `SwiftBarPlugins` 폴더를 선택합니다.

4. **홈 디렉토리 바로가기 생성 (선택 사항):**
   ```bash
   ln -sfn "$(pwd)/src" "$HOME/focus_project"
   ```

---

## 🚀 사용 방법

설치가 완료되면 3가지 방법 중 편리한 방식을 선택하여 사용할 수 있습니다.

### 방법 1: macOS 상단 메뉴바(SwiftBar)로 사용 (가장 편리함)
* **상태 확인:** 상단 메뉴바에 현재 상태가 표시됩니다.
  * `⚪ 집중모드 OFF` : 모니터링이 꺼진 상태
  * `🟢 집중모드 ON` : 모니터링이 켜져 차단 동작 중
* **메뉴 항목 클릭:**
  * **[집중모드 켜기 / 끄기]**: 클릭 즉시 모니터링 프로세스가 백그라운드에서 시작되거나 종료됩니다.
  * **[차단 목록 관리기(Manager) 열기]**: 터미널이 열리며 차단할 사이트/앱 목록을 바로 편집할 수 있습니다.

---

### 방법 2: 터미널 명령어로 사용
터미널에서 `make` 명령어를 통해 프로그램의 모든 기능을 직접 제어할 수 있습니다.

```bash
# 1. 차단 목록 편집기 열기 (웹사이트/앱 추가 및 삭제)
make run-manager

# 2. 백그라운드 집중 모니터 시작
make run-monitor

# 3. 현재 집중 모드 실행 여부 확인
make status

# 4. 백그라운드 집중 모니터 종료
make stop-monitor
```

---

### 방법 3: Xcode에서 열기
* 폴더 안의 `방중 프로젝트.xcodeproj` 파일을 더블 클릭하면 Xcode에서 프로젝트가 열립니다.
* Xcode 내부에서 `manager.cpp`와 `monitor.cpp` 코드를 확인하고 직접 빌드/디버깅할 수 있습니다.

---

## 📁 디렉토리 및 파일 구성

```text
방중 프로젝트/
├── Makefile                        # 원클릭 빌드, 설정(setup), 실행 제어 스크립트
├── README.md                       # 설치 및 사용 안내서 (본 파일)
├── .gitignore                      # Git 버전 관리 제외 목록
├── 방중 프로젝트.xcodeproj          # Xcode 프로젝트 파일
├── src/                            # 소스코드 심볼릭 링크 (터미널/Makefile용)
├── 방중 프로젝트/                  # C++ 소스 코드 및 차단 데이터 디렉토리
│   ├── manager.cpp                 # 차단 목록 관리 콘솔 프로그램 소스
│   ├── monitor.cpp                 # 백그라운드 차단 감시 데몬 소스
│   ├── web_list.txt                # 차단할 웹사이트 URL 도메인 목록
│   ├── proc_list.txt               # 차단할 프로세스(앱) 이름 목록
│   ├── focus_manager               # 컴파일된 관리기 실행 파일
│   └── focus_monitor               # 컴파일된 감시기 실행 파일
└── SwiftBarPlugins/                # SwiftBar 메뉴바 연동 플러그인
    └── focus_toggle.3s.sh          # 3초마다 메뉴바 상태를 갱신하는 쉘 스크립트
```

---

## 🛠️ Makefile 명령어 모음

| 명령어 | 설명 |
|---|---|
| `make setup` | **처음 설치 시 권장** (컴파일 + 실행 권한 + SwiftBar 연동 자동 세팅) |
| `make` 또는 `make all` | C++ 실행 파일 2종(`focus_manager`, `focus_monitor`) 컴파일 |
| `make run-manager` | 차단 목록 편집기 콘솔 화면 실행 |
| `make run-monitor` | 백그라운드 집중 감시 데몬 시작 |
| `make stop-monitor` | 실행 중인 집중 감시 데몬 종료 |
| `make status` | 현재 집중모드 ON/OFF 상태 확인 |
| `make clean` | 컴파일된 바이너리 삭제 |
| `make help` | 전체 명령어 도움말 출력 |

---

## ❓ 자주 묻는 질문 (FAQ) & 문제 해결

### Q1. `make` 실행 시 `clang++: command not found` 오류가 발생합니다.
> Mac에 개발자 도구가 설치되어 있지 않은 경우입니다. 터미널에 `xcode-select --install`을 입력하여 Command Line Tools를 설치한 후 다시 실행해 주세요.

### Q2. 메뉴바에 SwiftBar 아이콘이 나타나지 않아요.
> 1. Applications 폴더에서 `SwiftBar.app`이 실행 중인지 확인하세요.
> 2. SwiftBar 메뉴의 `Preferences...` -> `Change Plugin Folder...`에서 본 프로젝트의 `SwiftBarPlugins` 폴더를 직접 선택해 주시면 즉시 나타납니다.

### Q3. 프로세스나 웹사이트가 차단되지 않아요.
> 1. `make run-manager`를 실행하여 `web_list.txt`와 `proc_list.txt`에 올바른 프로세스 이름(예: `KakaoTalk`)이나 도메인이 등록되어 있는지 확인하세요.
> 2. `make status` 또는 메뉴바 아이콘이 `🟢 집중모드 ON` 상태인지 확인하세요.
