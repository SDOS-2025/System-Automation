all: 
	make -C src/portaudio/

	make -C src/whisper.cpp/
	src/whisper.cpp/models/download-ggml-model.sh base
	mkdir ~/.local/share/SystemAutomation/
	cp src/whisper.cpp/models/ggml-base.bin ~/.local/share/SystemAutomation/ 
	
	g++ src/STT.cpp src/MyApp.cpp -o MyApp `python3-config --cflags --ldflags` -lpython3.13 `pkg-config gtkmm-4.0 --cflags --libs` -lsqlite3 src/portaudio/lib/.libs/libportaudio.a src/whisper.cpp/build/src/libwhisper.a src/whisper.cpp/build/ggml/src/libggml.a src/whisper.cpp/build/ggml/src/libggml-base.a src/whisper.cpp/build/ggml/src/libggml-cpu.a -lasound -fopenmp
	mv MyApp ./build/
	mkdir ~/.config/SystemAutomation/

slim:
	g++ src/STT.cpp src/MyApp.cpp -o MyApp `python3-config --cflags --ldflags` -lpython3.13 `pkg-config gtkmm-4.0 --cflags --libs` -lsqlite3 src/portaudio/lib/.libs/libportaudio.a src/whisper.cpp/build/src/libwhisper.a src/whisper.cpp/build/ggml/src/libggml.a src/whisper.cpp/build/ggml/src/libggml-base.a src/whisper.cpp/build/ggml/src/libggml-cpu.a -lasound -fopenmp
	mv MyApp ./build/

clean-all:
	make clean -C src/portaudio/
	
	rm -rf src/whisper.cpp/build/
	rm -f src/whisper.cpp/models/ggml-base.bin
	
	rm -rf build/MyApp
	rm -rf ~/.config/SystemAutomation/
	rm -rf ~/.local/share/SystemAutomation/

clean: 
	rm -rf build/MyApp