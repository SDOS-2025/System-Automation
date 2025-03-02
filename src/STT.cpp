#include <bits/stdc++.h>
#include <iostream>
#include "portaudio/include/portaudio.h"
#include "whisper.cpp/include/whisper.h"
using namespace std;

#define SAMPLE_RATE 16000
#define FRAMES_PER_BUFFER 512
#define NUM_CHANNELS 1

struct AudioData{
    std::vector<float> buffer;
};

class STT{
    private:
        //all whisper and pa stuff
        PaStream* pStream;

        //callback - required for Pa audio record
        static int audioCallback(const void *inputBuffer, void *outputBuffer,
            unsigned long framesPerBuffer, const PaStreamCallbackTimeInfo *timeInfo,
            PaStreamCallbackFlags statusFlags, void *userData) {

            AudioData *data = (AudioData *) userData;
            const float *input = (const float *) inputBuffer;

            if (inputBuffer != nullptr) //appending to the buffer the input
                data->buffer.insert(data->buffer.end(), input, input + framesPerBuffer);

            return paContinue;
        }

    public:
        AudioData* pAudioData;

        STT(){
            pAudioData = new AudioData();
        }

        ~STT(){
            delete pAudioData;
        }

        void listen(){
            //Clear the buffer
            pAudioData -> buffer.clear();
            
            if (Pa_Initialize() != paNoError)
                throw runtime_error("Failed to initialize PortAudio");
        
            // Open audio stream
            if (Pa_OpenDefaultStream(&pStream, NUM_CHANNELS, 0, paFloat32, SAMPLE_RATE, FRAMES_PER_BUFFER, STT::audioCallback, pAudioData) != paNoError)
                throw runtime_error("Failed to open audio stream");
        
            // Start audio capture
            if (Pa_StartStream(pStream) != paNoError)
                throw runtime_error("Failed to start stream");
        
            std::cout << "Listening..." << std::endl;  
            return;
        }

        void stop(){
            Pa_StopStream(pStream); 
            Pa_CloseStream(pStream);
            Pa_Terminate();
            return;
        }

        //whisper part
        static string transcribe(AudioData* audioData){
            const char* homePath = getenv("HOME");
            string modelPath = string(homePath) + "/.local/share/SystemAutomation/ggml-base.bin";
            struct whisper_context_params params = whisper_context_default_params();
            struct whisper_context* whisperModel = whisper_init_from_file_with_params(modelPath.c_str(), params);
            struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
            string transcription = "";

            if (!whisperModel)
                throw runtime_error("Failed to initialize Whisper module!");
                    
            // Run Whisper transcription
            if (whisper_full(whisperModel, wparams, audioData -> buffer.data(), audioData -> buffer.size()) != 0)
                throw runtime_error("Failed to transcribe audio!");
            else{
                int segments = whisper_full_n_segments(whisperModel);
                for (int i = 0; i < segments; i++)
                    transcription += whisper_full_get_segment_text(whisperModel, i);
            }
        
            whisper_free(whisperModel);
            return transcription;
        }
};