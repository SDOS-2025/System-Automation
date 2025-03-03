CXX = g++
WHISPER_PATH = $(realpath ../../lib/whisper.cpp)
LDFLAGS = `pkg-config --libs gtkmm-3.0` -lsqlite3 -L$(WHISPER_PATH)/src \
          -L$(WHISPER_PATH)/ggml/src -lwhisper -lggml -lpthread -lasound -ldl
CXXFLAGS = `pkg-config --cflags gtkmm-3.0` -Wall -I$(WHISPER_PATH)/include -I$(WHISPER_PATH)/ggml/include

SRCS = MyApp.cpp AppDB.cpp Speech.cpp wav.cpp
OBJS = $(SRCS:.cpp=.o)
HEADERS = Speech.hpp Logger.hpp

# Add whisper source files
WHISPER_SRC = ../../lib/whisper.cpp/src/whisper.cpp

# Build whisper first
WHISPER_DIR = ../../lib/whisper.cpp
# WHISPER_LIB = $(WHISPER_DIR)/libwhisper.a

all: MyApp

# $(WHISPER_LIB):
# 	$(MAKE) -C $(WHISPER_DIR) libwhisper.a

# WHISPER_LIB = $(WHISPER_PATH)/libwhisper.a

$(WHISPER_LIB):
	$(MAKE) -C $(WHISPER_DIR) libwhisper.a

MyApp: MyApp.cpp AppDB.cpp Speech.cpp wav.cpp
	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS) -Wl,-rpath,$(WHISPER_PATH)/src:$(WHISPER_PATH)/ggml/src

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f MyApp $(OBJS)
	# rm -rf $(WHISPER_PATH)/build  # Clean CMake build directory