all: 
	# Create src directory if it doesn't exist
	mkdir -p src

	# Clone whisper.cpp repository if it doesn't exist
	test -d src/whisper.cpp || git clone https://github.com/ggml-org/whisper.cpp.git src/whisper.cpp

	make -C src/portaudio/

	make -C src/whisper.cpp/
	src/whisper.cpp/models/download-ggml-model.sh base
	mkdir -p ~/.local/share/SystemAutomation/ 2>/dev/null || true
	cp src/whisper.cpp/models/ggml-base.bin ~/.local/share/SystemAutomation/ 
	
	g++ src/STT.cpp src/MyApp.cpp -o MyApp `python3-config --cflags --ldflags` -lpython3.12 `pkg-config gtkmm-4.0 --cflags --libs` -lsqlite3 src/portaudio/lib/.libs/libportaudio.a src/whisper.cpp/build/src/libwhisper.so src/whisper.cpp/build/ggml/src/libggml.so src/whisper.cpp/build/ggml/src/libggml-base.so src/whisper.cpp/build/ggml/src/libggml-cpu.so -lasound -ljack -fopenmp -Isrc/whisper.cpp/include -Isrc/whisper.cpp/ggml/include
	mv MyApp ./build/
	mkdir -p ~/.config/SystemAutomation/ 2>/dev/null || true
	# Copy required shared libraries to the build directory for runtime
	cp src/whisper.cpp/build/src/libwhisper.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml-base.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml-cpu.so ./build/
	# Create symbolic links with the correct SONAME version
	cd ./build && ln -sf libwhisper.so libwhisper.so.1
	cd ./build && ln -sf libggml.so libggml.so.1
	cd ./build && ln -sf libggml-base.so libggml-base.so.1
	cd ./build && ln -sf libggml-cpu.so libggml-cpu.so.1

slim:
	g++ src/STT.cpp src/MyApp.cpp -o MyApp `python3-config --cflags --ldflags` -lpython3.12 `pkg-config gtkmm-4.0 --cflags --libs` -lsqlite3 src/portaudio/lib/.libs/libportaudio.a src/whisper.cpp/build/src/libwhisper.so src/whisper.cpp/build/ggml/src/libggml.so src/whisper.cpp/build/ggml/src/libggml-base.so src/whisper.cpp/build/ggml/src/libggml-cpu.so -lasound -ljack -fopenmp -Isrc/whisper.cpp/include -Isrc/whisper.cpp/ggml/include
	mv MyApp ./build/
	# Copy required shared libraries to the build directory for runtime
	cp src/whisper.cpp/build/src/libwhisper.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml-base.so ./build/
	cp src/whisper.cpp/build/ggml/src/libggml-cpu.so ./build/
	# Create symbolic links with the correct SONAME version
	cd ./build && ln -sf libwhisper.so libwhisper.so.1
	cd ./build && ln -sf libggml.so libggml.so.1
	cd ./build && ln -sf libggml-base.so libggml-base.so.1
	cd ./build && ln -sf libggml-cpu.so libggml-cpu.so.1

clean-all:
	make clean -C src/portaudio/
	
	rm -rf src/whisper.cpp/build/
	rm -f src/whisper.cpp/models/ggml-base.bin
	
	rm -rf build/MyApp
	rm -rf ~/.config/SystemAutomation/
	rm -rf ~/.local/share/SystemAutomation/

clean: 
	rm -rf build/MyApp