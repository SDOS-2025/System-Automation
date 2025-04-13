CXX = g++
# Add C++17 standard
CXXFLAGS = `pkg-config --cflags gtkmm-3.0` -Wall -I$(WHISPER_PATH)/include -I$(WHISPER_PATH)/ggml/include -std=c++17 -pthread
WHISPER_PATH = $(realpath ../../lib/whisper.cpp)
# Add sqlite3 and pthread to LDFLAGS for application
APP_LDFLAGS = `pkg-config --libs gtkmm-3.0` -lsqlite3 -L$(WHISPER_PATH)/src \
          -L$(WHISPER_PATH)/ggml/src -lwhisper -lggml -lpthread -lasound -ldl

# Google Test setup
GTEST_DIR = ../../lib/googletest
GTEST_SRC_DIR = $(GTEST_DIR)/googletest
GTEST_INCLUDE = -I$(GTEST_DIR)/googletest/include -I$(GTEST_DIR)/googlemock/include
GTEST_LIB_DIR = $(GTEST_DIR)/build/lib
GTEST_LIBS = $(GTEST_LIB_DIR)/libgtest.a $(GTEST_LIB_DIR)/libgtest_main.a
# Test specific LDFLAGS
TEST_LDFLAGS = -lsqlite3 -lpthread -L. # Link sqlite3 and pthread for tests, look for libs in current dir

# Source files for main application
SRCS = MyApp.cpp AppDB.cpp Speech.cpp wav.cpp
OBJS = $(SRCS:.cpp=.o)
HEADERS = Speech.hpp Logger.hpp wav.h # Added wav.h

# Test source files
TEST_SRCS = ../../tests/AppDB_test.cpp
TEST_OBJS = $(TEST_SRCS:.cpp=.o)
APP_DB_OBJ = AppDB.o # Object file for the class under test
TEST_EXECUTABLE = appdb_test_runner

# Add whisper source files
WHISPER_SRC = ../../lib/whisper.cpp/src/whisper.cpp

# Build whisper first
WHISPER_DIR = ../../lib/whisper.cpp
WHISPER_LIB = $(WHISPER_DIR)/libwhisper.a

# Main application target
all: MyApp test # Build app and test runner by default

# Google Test library target
$(GTEST_LIBS): | $(GTEST_DIR)
	@echo "Building Google Test..."
	@cmake -S $(GTEST_SRC_DIR) -B $(GTEST_DIR)/build -DCMAKE_INSTALL_PREFIX=$(GTEST_DIR)/install
	@$(MAKE) -C $(GTEST_DIR)/build

# Rule to clone Google Test if directory doesn't exist
$(GTEST_DIR):
	@echo "Google Test not found. Cloning repository..."
	@git clone https://github.com/google/googletest.git $(GTEST_DIR)

# Whispepr library target
$(WHISPER_LIB):
	$(MAKE) -C $(WHISPER_DIR) libwhisper.a

# Main application build rule
MyApp: $(OBJS) $(WHISPER_LIB) # Depends on object files and whisper lib
	$(CXX) -o $@ $(filter %.o, $^) $(CXXFLAGS) $(APP_LDFLAGS) -Wl,-rpath,$(WHISPER_PATH)/src:$(WHISPER_PATH)/ggml/src

# Rule to build AppDB object file separately
$(APP_DB_OBJ): AppDB.cpp # Remove AppDB.h dependency
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Rule to build test object files
$(TEST_OBJS): ../../tests/AppDB_test.cpp $(APP_DB_OBJ) | $(GTEST_DIR) # Remove AppDB.h dependency, Add order-only prerequisite for gtest dir
	$(CXX) $(CXXFLAGS) $(GTEST_INCLUDE) -c $< -o $@

# Rule to build the test executable
$(TEST_EXECUTABLE): $(TEST_OBJS) $(APP_DB_OBJ) $(GTEST_LIBS)
	$(CXX) -o $@ $(filter %.o, $^) $(TEST_LDFLAGS) $(GTEST_LIBS) -lstdc++fs # Link test objects, AppDB obj, gtest, sqlite, pthread, and stdc++fs

# Test execution target
test: $(TEST_EXECUTABLE)
	@echo "Running AppDB tests..."
	./$(TEST_EXECUTABLE)

# Generic object file rule
%.o: %.cpp $(HEADERS) # Added header dependency
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f MyApp $(OBJS) $(TEST_EXECUTABLE) $(TEST_OBJS) $(APP_DB_OBJ) user.db test_user.db # Clean app, objects, test runner, test objects, AppDB object, and test dbs
	# Optionally clean gtest build artifacts
	# rm -rf $(GTEST_DIR)/build $(GTEST_DIR)/install
	# rm -rf $(WHISPER_PATH)/build  # Clean CMake build directory