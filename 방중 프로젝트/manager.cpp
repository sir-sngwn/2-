//
//  manager.cpp
//  방중 프로젝트
//
//  Created by 김성원의 맥 on 11/22/26.
//
#include <iostream>
#include <fstream>
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
};

class webBlocker : public getFocused {
    vector<blockWeb> webList;
    string filename;
public:
    webBlocker(const string& file = "web_list.txt") : filename(file) {
        ifstream fileStream(filename);
        if (!fileStream.is_open()) {
            addNew("유튜브", "youtube.com");
            addNew("인스타릴스", "instagram.com/reels/");
        } else {
            string name, url;
            while (fileStream >> name >> url) {
                webList.push_back({name, url});
            }
        }
    }

    void saveToFile() {
        ofstream fileStream(filename);
        for (const auto& w : webList) {
            fileStream << w.name << " " << w.URL << "\n";
        }
    }

    bool deleteItem(const string &n) override {
        for (size_t i = 0; i < webList.size(); ++i) {
            if (webList[i].name == n || webList[i].URL == n) {
                webList.erase(webList.begin() + i);
                saveToFile();
                return true;
            }
        }
        return false;
    }

    void addNew(const string &n, const string &u) {
        webList.push_back({n, u});
        saveToFile();
    }

    void printList() const override {
        for (const auto& w : webList) {
            cout << "- " << w.name << " : " << w.URL << "\n";
        }
    }
};

class processBlocker : public getFocused {
    vector<blockProcess> processList;
    string filename;
public:
    processBlocker(const string& file = "proc_list.txt") : filename(file) {
        ifstream fileStream(filename);
        if (!fileStream.is_open()) {
            addNew("steam");
        } else {
            string name;
            while (fileStream >> name) {
                processList.push_back({name});
            }
        }
    }

    void saveToFile() {
        ofstream fileStream(filename);
        for (const auto& p : processList) {
            fileStream << p.name << "\n";
        }
    }

    bool deleteItem(const string &n) override {
        for (size_t i = 0; i < processList.size(); ++i) {
            if (processList[i].name == n) {
                processList.erase(processList.begin() + i);
                saveToFile();
                return true;
            }
        }
        return false;
    }

    void addNew(const string &n) {
        processList.push_back({n});
        saveToFile();
    }

    void printList() const override {
        for (const auto& p : processList) {
            cout << "- " << p.name << "\n";
        }
    }
};

int main(int argc, char* argv[]) {
    string baseDir = (argc > 1) ? string(argv[1]) + "/" : "";
    webBlocker wb(baseDir + "web_list.txt");
    processBlocker pb(baseDir + "proc_list.txt");
    string menu = "";

    while (true) {
        cout << "\n=== management command list ===\n";
        cout << "print_web\n";
        cout << "add_web\n";
        cout << "print_proc\n";
        cout << "add_proc\n";
        cout << "delete\n";
        cout << "end\n";
        cout << ": ";
        cin >> menu;

        if (menu == "end") {
            break;
        }
        else if (menu == "print_web") {
            cout << "\n[Blocked Web List]\n";
            wb.printList();
        }
        else if (menu == "add_web") {
            string name, url;
            cout << "web name (띄어쓰기 없이 or cancel): ";
            cin >> name;
            if (name == "cancel") continue;
            cout << "URL : ";
            cin >> url;
            wb.addNew(name, url);
            cout << "complete !\n";
        }
        else if (menu == "print_proc") {
            cout << "\n[Blocked Process List]\n";
            pb.printList();
        }
        else if (menu == "add_proc") {
            string name;
            cout << "proc name (or cancel): ";
            cin >> name;
            if (name == "cancel") continue;
            pb.addNew(name);
            cout << "complete!\n";
        }
        else if (menu == "delete") {
            string target;
            cout << "target name or URL (or cancel): ";
            cin >> target;
            if (target == "cancel") continue;
            if (wb.deleteItem(target) || pb.deleteItem(target)) {
                cout << "complete!\n";
            }
            else {
                cout << "not in the list.\n";
            }
        }
        else {
            cout << "invalid command\n";
        }
    }
    return 0;
}
