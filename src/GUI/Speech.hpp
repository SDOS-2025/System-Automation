#pragma once
#include "../../lib/whisper.cpp/include/whisper.h"
#include <alsa/asoundlib.h>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

class Speech {
private:
    struct whisper_context* ctx;
    bool isInitialized;
    snd_pcm_t* capture_handle;
    std::vector<float> audio_buffer;
    bool m_is_recording;
    std::thread audio_thread;
    std::mutex m_mutex;
    snd_pcm_t* m_pcm;
    std::thread m_audio_thread;
    void cleanupALSA();
    void processAudio();

public:
    bool isRecording() const { return m_is_recording; }
    Speech();
    ~Speech();
    bool init();
    void startRecording();
    void stopRecording();
    std::string transcribe(const std::string& audioFile);
    std::string transcribe_buffer();
};