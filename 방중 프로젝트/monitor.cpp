//
//  monitor.cpp
//  방중 프로젝트
//
//  Created by 김성원의 맥 on 11/22/26.
//
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <cstdlib>
#include <unistd.h>

using namespace std;

struct blockWeb {
    string name;
    string URL;
};

struct blockProcess {
    string name;
};

class getFocused {
public:
    virtual ~getFocused() = default;
    virtual void loadFromFile(const string& filename) = 0;
    virtual bool isRunning() = 0;
};

class webBlocker : public getFocused {
    vector<blockWeb> webList;
public:
    void loadFromFile(const string& filename) override {
        webList.clear();
        ifstream file(filename);
        if (!file.is_open()) {
            webList.push_back({"유튜브쇼츠", "youtube.com/shorts/"});
            webList.push_back({"인스타릴스", "instagram.com/reels/"});
            return;
        }
        string name, url;
        while (file >> name >> url) {
            webList.push_back({name, url});
        }
    }

    bool isRunning() override {
        string cmd = "osascript -e '"
                     "set res to \"\"\n"
                     "if application \"Google Chrome\" is running then\n"
                     "    tell application \"Google Chrome\"\n"
                     "        set res to res & (URL of active tab of every window as string) & \" \"\n"
                     "    end tell\n"
                     "end if\n"
                     "if application \"Safari\" is running then\n"
                     "    tell application \"Safari\"\n"
                     "        set res to res & (URL of every document as string) & \" \"\n"
                     "    end tell\n"
                     "end if\n"
                     "return res"
                     "' 2>/dev/null";

        FILE* pipe = popen(cmd.c_str(), "r");
        if (!pipe) return false;

        char buffer[512];
        string currentUrls = "";
        while (fgets(buffer, sizeof(buffer), pipe) != NULL) {
            currentUrls += buffer;
        }
        pclose(pipe);

        for (const auto& web : webList) {
            if (!web.URL.empty() && currentUrls.find(web.URL) != string::npos) {
                return true;
            }
        }
        return false;
    }
};

class processBlocker : public getFocused {
    vector<blockProcess> processList;
public:
    void loadFromFile(const string& filename) override {
        processList.clear();
        ifstream file(filename);
        if (!file.is_open()) {
            processList.push_back({"steam"});
            return;
        }
        string name;
        while (file >> name) {
            processList.push_back({name});
        }
    }

    bool isRunning() override {
        for (const auto& proc : processList) {
            if (proc.name.empty()) continue;
            string cmd = "pgrep -i \"" + proc.name + "\" > /dev/null 2>&1";
            if (system(cmd.c_str()) == 0) {
                return true;
            }
        }
        return false;
    }
};

string getPetHtmlPath(const string& baseDir) {
    const char* home = getenv("HOME");
    string homeStr = home ? string(home) : "";

    vector<string> candidates = {
        baseDir + "pet/pet.html",
        baseDir + "../pet/pet.html",
        homeStr + "/focus_project/pet/pet.html",
        homeStr + "/Desktop/방중 프로젝트/pet/pet.html"
    };

    for (const auto& path : candidates) {
        if (access(path.c_str(), R_OK) == 0) {
            return path;
        }
    }
    return baseDir + "pet/pet.html";
}

void showPopup(const string& htmlPath) {
    if (htmlPath.empty()) return;
    
    string checkCmd = "pgrep -f 'user-data-dir=/tmp/focus_pet' > /dev/null 2>&1";
    if (system(checkCmd.c_str()) == 0) {
        return;
    }

    string cmd = "open -na \"Google Chrome\" --args --user-data-dir=/tmp/focus_pet --app=\"file://" 
                 + htmlPath + "\" --window-size=300,300 > /dev/null 2>&1 &";
    int res = system(cmd.c_str());
    if (res != 0) {
        string fallback = "open \"" + htmlPath + "\" > /dev/null 2>&1 &";
        system(fallback.c_str());
    }
}
void hidePopup() {
    string checkCmd = "pgrep -f 'user-data-dir=/tmp/focus_pet' > /dev/null 2>&1";
    if (system(checkCmd.c_str()) == 0) {
        system("pkill -9 -f 'user-data-dir=/tmp/focus_pet' > /dev/null 2>&1");
    }
}

int main(int argc, char* argv[]) {
    string baseDir = (argc > 1) ? string(argv[1]) + "/" : "";
    string webFile = baseDir + "web_list.txt";
    string procFile = baseDir + "proc_list.txt";
    string htmlPath = getPetHtmlPath(baseDir);

    webBlocker wb;
    processBlocker pb;

    while (true) {
        wb.loadFromFile(webFile);
        pb.loadFromFile(procFile);

        bool detected = wb.isRunning() || pb.isRunning();
        if (detected) {
            showPopup(htmlPath);
        } else {
            hidePopup();
        }

        this_thread::sleep_for(chrono::seconds(3));
    }

    return 0;
}
