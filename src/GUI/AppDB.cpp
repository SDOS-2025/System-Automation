#include <sqlite3.h>
#include <bits/stdc++.h>

using namespace std;
class AppDB{
    private:
        sqlite3* dbPointer;
        char* error;
        const char* sql;
        sqlite3_stmt* rows;

    public:
        AppDB(){
            if(sqlite3_open("user.db", &dbPointer) != SQLITE_OK)
                throw 1; //1st exception

            //Create Default table If it does not exist
            sql = R"(CREATE TABLE IF NOT EXISTS settings (
                                    id INT NOT NULL UNIQUE,
                                    key TEXT,
                                    sensVal DECIMAL(2, 1),
                                    PRIMARY KEY(id)
                                );
                                CREATE TABLE IF NOT EXISTS history (
                                    id INT NOT NULL UNIQUE,
                                    time TIMESTAMP,
                                    input TEXT,
                                    PRIMARY KEY(id)
                                );
                                CREATE TABLE IF NOT EXISTS screenshots(
                                    id INT NOT NULL UNIQUE,
                                    historyID INT,
                                    BLOB ss,
                                    PRIMARY KEY(id),
                                    FOREIGN KEY (historyID) REFERENCES history(id)
                                );
                                CREATE TABLE IF NOT EXISTS presets(
                                    id INT NOT NULL UNIQUE,
                                    presetName TEXT UNIQUE,
                                    commands TEXT,
                                    PRIMARY KEY(id)
                                );)";

            if(sqlite3_exec(dbPointer, sql, nullptr, nullptr, &error) != SQLITE_OK){
                cout << error << endl;
                throw 2;
            }


            //check if the settings table is empty, else insert default values
            sql = R"(SELECT COUNT(*) FROM SETTINGS)";
            int count;
            if(sqlite3_prepare_v2(dbPointer, sql, -1, &rows, nullptr) == SQLITE_OK){
                while(sqlite3_step(rows) == SQLITE_ROW){
                    count = sqlite3_column_int(rows, 0);
                }
            }

            //insert default values if required
            if(count == 0){
                sql = R"(INSERT INTO settings (id, key, sensVal) VALUES (0, "ABCD-EFGH-IJKL", 0.5);)";
                if(sqlite3_exec(dbPointer, sql, nullptr, nullptr, &error) != SQLITE_OK){
                    cout << error << endl;
                    throw 2;
                }
            }
        }

        string fetchSettingsAPI(){
            const char* apiKey = nullptr;
            sql = "SELECT key FROM settings";
            if(sqlite3_prepare_v2(dbPointer, sql, -1, &rows, nullptr) == SQLITE_OK){
                while(sqlite3_step(rows) == SQLITE_ROW){
                    apiKey = reinterpret_cast<const char*>(sqlite3_column_text(rows, 0));
                    return std::string(apiKey);
                }
            }  
        }
        
        float fetchSettingsSens(){
            sql = "SELECT sensVal FROM settings";
            float sensVal = 0;
            if(sqlite3_prepare_v2(dbPointer, sql, -1, &rows, nullptr) == SQLITE_OK){
                while(sqlite3_step(rows) == SQLITE_ROW){
                    sensVal = sqlite3_column_double(rows, 0);
                }
            }
            return sensVal;        
        }

        void updateSettings(string apiKey, float sensVal){
            string localSQL = "UPDATE settings SET key = '" + apiKey + "', sensVal = "+ to_string(sensVal) + " WHERE id = 0";
            cout << localSQL << endl;
            if(sqlite3_exec(dbPointer, localSQL.c_str(), nullptr, nullptr, &error) != SQLITE_OK){
                cout << error << endl;
                throw 2;
            }
        }

        void updateSettings(float sensVal){
            string localSQL = "UPDATE settings SET sensVal = "+ to_string(sensVal) + " WHERE id = 0";
            cout << localSQL << endl;
            if(sqlite3_exec(dbPointer, localSQL.c_str(), nullptr, nullptr, &error) != SQLITE_OK){
                cout << error << endl;
                throw 2;
            }
        }

        void updatePresets(string name, string command){
            sql = "SELECT COUNT(*) FROM presets";
            int rowCount;
            if(sqlite3_prepare_v2(dbPointer, sql, -1, &rows, nullptr) == SQLITE_OK){
                while(sqlite3_step(rows) == SQLITE_ROW){
                    rowCount = sqlite3_column_double(rows, 0);
                }
            }
            string localSQL = "INSERT INTO presets (id, presetName, commands) VALUES (" + to_string(rowCount) + ", " + "\"" + name + "\"" + ", " + "\"" + command + "\"" + ");";
            cout << localSQL << endl;
            if(sqlite3_exec(dbPointer, localSQL.c_str(), nullptr, nullptr, &error) != SQLITE_OK){
                cout << error << endl;
                throw 2;
            }
        }

        vector<vector<string>> fetchPresets(){
            vector<vector<string>> queryResult;
            sql = "SELECT * FROM presets;";
            if(sqlite3_prepare_v2(dbPointer, sql, -1, &rows, nullptr) == SQLITE_OK){
                while(sqlite3_step(rows) == SQLITE_ROW){
                    vector<string> currRow;
                    currRow.push_back(to_string((sqlite3_column_int(rows, 0))));
                    currRow.push_back(string(reinterpret_cast<const char*>(sqlite3_column_text(rows, 1))));
                    currRow.push_back(string(reinterpret_cast<const char*>(sqlite3_column_text(rows, 2))));
                    queryResult.push_back(currRow);
                }
            }
            return queryResult;
        }

        void clearPresets(){
            sql = "DELETE FROM presets;";
            if(sqlite3_exec(dbPointer, sql, nullptr, nullptr, &error) != SQLITE_OK){
                cout << error << endl;
                throw 2;
            }
        }
};

/*
#include <iostream>
#include <sqlite3.h>

int main() {
    sqlite3* db;
    char* errMsg = nullptr;

    // Open (or create) a database
    if (sqlite3_open("example.db", &db) != SQLITE_OK) {
        std::cerr << "Error opening database: " << sqlite3_errmsg(db) << std::endl;
        return 1;
    }

    // Create a table
    const char* sql = "CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT);";
    if (sqlite3_exec(db, sql, nullptr, nullptr, &errMsg) != SQLITE_OK) {
        std::cerr << "Error creating table: " << errMsg << std::endl;
        sqlite3_free(errMsg);
    }

    // Insert a record
    sql = "INSERT INTO users (name) VALUES ('Alice');";
    if (sqlite3_exec(db, sql, nullptr, nullptr, &errMsg) != SQLITE_OK) {
        std::cerr << "Error inserting record: " << errMsg << std::endl;
        sqlite3_free(errMsg);
    }

    // Query the data
    sqlite3_stmt* stmt;
    sql = "SELECT * FROM users;";
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            int id = sqlite3_column_int(stmt, 0);
            const char* name = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
            std::cout << "User: " << id << " - " << name << std::endl;
        }
        sqlite3_finalize(stmt);
    } else {
        std::cerr << "Error executing query" << std::endl;
    }

    // Close database
    sqlite3_close(db);
    return 0;
}

*/