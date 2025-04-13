#include "../src/GUI/AppDB.cpp" // Include the source file directly for simplicity, or compile separately and link
#include <filesystem> // Requires C++17
#include <fstream>
#include <gtest/gtest.h>
#include <sqlite3.h>

// Define a test fixture for AppDB tests
class AppDBTest : public ::testing::Test {
protected:
    // Per-test-suite set-up.
    // Called before the first test in this test suite.
    static void SetUpTestSuite()
    {
        // Create a temporary database file for testing
        std::ofstream outfile(testDbName);
        outfile.close();
    }

    // Per-test-suite tear-down.
    // Called after the last test in this test suite.
    static void TearDownTestSuite()
    {
        // Clean up the temporary database file
        std::filesystem::remove(testDbName);
    }

    // You can define per-test set-up and tear-down logic using
    // SetUp() and TearDown() methods.
    void SetUp() override
    {
        // Ensure the test database is clean before each test if needed
        // For AppDB, the constructor handles table creation, maybe just delete/recreate?
        std::filesystem::remove(testDbName); // Remove previous
        std::ofstream outfile(testDbName); // Create new empty
        outfile.close();

        // Redirect sqlite3_open to use the test database name
        // This is tricky without modifying AppDB or using linking tricks.
        // Option 1: Modify AppDB to accept a db name in the constructor (preferred).
        // Option 2: Use a different name in AppDB constructor temporarily.
        // Option 3: Linker substitution (complex).
        // For now, let's assume we modify AppDB to take the db name.
        // Or, we can just let it create/use 'user.db' and clean it up.
        // Let's stick with the default 'user.db' for now and clean it up.
        std::filesystem::remove("user.db"); // Clean up potential previous runs
    }

    void TearDown() override
    {
        // Clean up the default database file after each test
        std::filesystem::remove("user.db");
    }

    // Objects declared here can be used by all tests in the test suite.
    // AppDB db; // Be careful: constructor throws, handle potential setup issues

    static const char* testDbName; // Or maybe just use "user.db" and clean up
};

const char* AppDBTest::testDbName = "test_user.db"; // Let's try using the default name in tests

// Placeholder Test Case
TEST_F(AppDBTest, ConstructorCreatesTables)
{
    // Arrange: Clean state ensured by SetUp

    // Act: Create an AppDB instance. This should create the db and tables.
    ASSERT_NO_THROW({
        AppDB db; // Use default constructor, which uses "user.db"
    });

    // Assert: Check if the tables were created in "user.db"
    sqlite3* dbPointer;
    ASSERT_EQ(sqlite3_open("user.db", &dbPointer), SQLITE_OK);

    sqlite3_stmt* stmt;
    // Check settings table
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT COUNT(*) FROM settings;", -1, &stmt, nullptr), SQLITE_OK);
    ASSERT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    EXPECT_EQ(sqlite3_column_int(stmt, 0), 1); // Should have 1 default row
    sqlite3_finalize(stmt);

    // Check history table
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT sql FROM sqlite_master WHERE type='table' AND name='history';", -1, &stmt, nullptr), SQLITE_OK);
    EXPECT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    sqlite3_finalize(stmt);

    // Check screenshots table
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT sql FROM sqlite_master WHERE type='table' AND name='screenshots';", -1, &stmt, nullptr), SQLITE_OK);
    EXPECT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    sqlite3_finalize(stmt);

    // Check presets table
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT sql FROM sqlite_master WHERE type='table' AND name='presets';", -1, &stmt, nullptr), SQLITE_OK);
    EXPECT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    sqlite3_finalize(stmt);

    sqlite3_close(dbPointer);
}

// Add more tests for fetchSettingsAPI, fetchSettingsSens, updateSettings, etc.

// Example test for fetchSettingsAPI
TEST_F(AppDBTest, FetchSettingsAPI_Default)
{
    // Arrange
    AppDB db; // Creates db with default settings

    // Act
    std::string apiKey = db.fetchSettingsAPI();

    // Assert
    EXPECT_EQ(apiKey, "ABCD-EFGH-IJKL");
}

// Example test for fetchSettingsSens
TEST_F(AppDBTest, FetchSettingsSens_Default)
{
    // Arrange
    AppDB db;

    // Act
    float sens = db.fetchSettingsSens();

    // Assert
    EXPECT_FLOAT_EQ(sens, 0.5f);
}

// Test for updating settings
TEST_F(AppDBTest, UpdateSettings_Both)
{
    // Arrange
    AppDB db;
    std::string newApiKey = "NEW-KEY-1234";
    float newSens = 0.8f;

    // Act
    ASSERT_NO_THROW({
        db.updateSettings(newApiKey, newSens);
    });

    // Assert
    EXPECT_EQ(db.fetchSettingsAPI(), newApiKey);
    EXPECT_FLOAT_EQ(db.fetchSettingsSens(), newSens);

    // Verify directly in DB
    sqlite3* dbPointer;
    ASSERT_EQ(sqlite3_open("user.db", &dbPointer), SQLITE_OK);
    sqlite3_stmt* stmt;
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT key, sensVal FROM settings WHERE id = 0;", -1, &stmt, nullptr), SQLITE_OK);
    ASSERT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    EXPECT_STREQ(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)), newApiKey.c_str());
    EXPECT_FLOAT_EQ(sqlite3_column_double(stmt, 1), newSens);
    sqlite3_finalize(stmt);
    sqlite3_close(dbPointer);
}

// Test for updating only sensitivity
TEST_F(AppDBTest, UpdateSettings_SensOnly)
{
    // Arrange
    AppDB db; // Default API key = "ABCD-EFGH-IJKL", sens = 0.5
    float newSens = 0.9f;

    // Act
    ASSERT_NO_THROW({
        db.updateSettings(newSens);
    });

    // Assert
    EXPECT_EQ(db.fetchSettingsAPI(), "ABCD-EFGH-IJKL"); // API key should not change
    EXPECT_FLOAT_EQ(db.fetchSettingsSens(), newSens);

    // Verify directly in DB
    sqlite3* dbPointer;
    ASSERT_EQ(sqlite3_open("user.db", &dbPointer), SQLITE_OK);
    sqlite3_stmt* stmt;
    ASSERT_EQ(sqlite3_prepare_v2(dbPointer, "SELECT key, sensVal FROM settings WHERE id = 0;", -1, &stmt, nullptr), SQLITE_OK);
    ASSERT_EQ(sqlite3_step(stmt), SQLITE_ROW);
    EXPECT_STREQ(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)), "ABCD-EFGH-IJKL");
    EXPECT_FLOAT_EQ(sqlite3_column_double(stmt, 1), newSens);
    sqlite3_finalize(stmt);
    sqlite3_close(dbPointer);
}

// Test for adding presets
TEST_F(AppDBTest, UpdatePresets_AddNew)
{
    // Arrange
    AppDB db;
    std::string presetName = "MyPreset";
    std::string presetCommands = "command1; command2";

    // Act
    ASSERT_NO_THROW({
        db.updatePresets(presetName, presetCommands);
    });

    // Assert
    std::vector<std::vector<std::string>> presets = db.fetchPresets();
    ASSERT_EQ(presets.size(), 1);
    EXPECT_EQ(presets[0].size(), 3);
    // ID might be 0 based on the faulty count logic, let's check name and command
    EXPECT_EQ(presets[0][1], presetName);
    EXPECT_EQ(presets[0][2], presetCommands);

    // Add another
    std::string presetName2 = "AnotherPreset";
    std::string presetCommands2 = "cmd3";
    ASSERT_NO_THROW({
        db.updatePresets(presetName2, presetCommands2);
    });

    presets = db.fetchPresets();
    ASSERT_EQ(presets.size(), 2);
    // Check the second preset (order might not be guaranteed, but likely insertion order)
    // The ID logic in AppDB::updatePresets is flawed (uses count before insert), so IDs might be 0, 1...
    EXPECT_EQ(presets[1][1], presetName2);
    EXPECT_EQ(presets[1][2], presetCommands2);
}

// Test fetching presets when none exist
TEST_F(AppDBTest, FetchPresets_Empty)
{
    // Arrange
    AppDB db;
    // Need to delete the default preset table content if any, or ensure it's empty.
    // The constructor doesn't add presets, so it should be empty initially.

    // Act
    std::vector<std::vector<std::string>> presets = db.fetchPresets();

    // Assert
    EXPECT_TRUE(presets.empty());
}

// Test fetching presets with multiple entries
TEST_F(AppDBTest, FetchPresets_Multiple)
{
    // Arrange
    AppDB db;
    db.updatePresets("Preset1", "cmd1");
    db.updatePresets("Preset2", "cmd2a;cmd2b");
    db.updatePresets("Preset3", "cmd3");

    // Act
    std::vector<std::vector<std::string>> presets = db.fetchPresets();

    // Assert
    ASSERT_EQ(presets.size(), 3);
    // We can check for specific presets, assuming the fetch order is consistent or searching the result vector
    bool found1 = false, found2 = false, found3 = false;
    for (const auto& p : presets) {
        if (p[1] == "Preset1" && p[2] == "cmd1")
            found1 = true;
        if (p[1] == "Preset2" && p[2] == "cmd2a;cmd2b")
            found2 = true;
        if (p[1] == "Preset3" && p[2] == "cmd3")
            found3 = true;
    }
    EXPECT_TRUE(found1);
    EXPECT_TRUE(found2);
    EXPECT_TRUE(found3);
}

// Entry point for running the tests
int main(int argc, char** argv)
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}