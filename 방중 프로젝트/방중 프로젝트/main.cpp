//
//  main.cpp
//  방중 프로젝트
//
//  Created by 김성원의 맥 on 9/3/26.
//


#include <iostream>
#include <string>
#include <vector>
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
    virtual bool deleteItem(const string &n) = 0;
    virtual void printList() const = 0;
    virtual bool isRunning() = 0;
};


class webBlocker : public getFocused {
    vector<blockWeb> webList;
public:
    webBlocker() {
            addNew("유튜브 쇼츠", "youtube.com/shorts/");
            addNew("인스타 릴스", "instagram.com/reels/");
        }
    
    bool deleteItem(const string &n) override{
        for (size_t i = 0; i < webList.size(); ++i) {
                    if (webList[i].name == n || webList[i].URL == n) {
                        webList.erase(webList.begin() + i);
                        return true;
                    }
                }
                return false;
    }
    void addNew(const string &n, const string &u) {
        webList.push_back({n, u});
    }
    
//    bool isRunning() override{
//        string cmd = "osascript -e 'tell application \"Google Chrome\" to return URL of active tab of front window' 2>/dev/null";
//        FILE* pipe = popen(cmd.c_str(), "r");
//        if (!pipe) return false;
//        char buffer[128];
//        
//        std::string currentUrl = "";
//        while (fgets(buffer, sizeof(buffer), pipe) != NULL) {
//            currentUrl += buffer;
//        }
//        pclose(pipe);
//        for (const auto& web : webList) {
//        if (!currentUrl.empty() && currentUrl.find(web.URL) != string::npos) {
//            return true;
//            }
//        }
//        return false;
//    }
};

class processBlocker : public getFocused {
    vector<blockProcess> processList;
public:
    processBlocker() {
            addNew("steam");
        }
    
    bool deleteItem(const string &n) override{
        for (size_t i = 0; i < processList.size(); ++i) {
                    if (processList[i].name == n) {
                        processList.erase(processList.begin() + i);
                        return true;
                        }
                    }
                return false;
    }
    
    void addNew(const string &n){
            processList.push_back({n});
    }
    
//    bool isRunning() override{
//        for (const auto& proc : processList) {
//            string cmd = "pgrep -i " + proc.name + " > /dev/null 2>&1";
//            int result = system(cmd.c_str());
//        }
//        return false;
//            }
};
