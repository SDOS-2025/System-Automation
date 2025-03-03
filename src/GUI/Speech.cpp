#include "Speech.hpp"
#include "Logger.hpp"
#include "wav.h"
#include "whisper.h"
#include <alsa/asoundlib.h>
#include <filesystem>
#include <iostream>
#include <thread>

Speech::Speech()
    : ctx(nullptr)
    , isInitialized(false)
    , capture_handle(nullptr)
    , m_is_recording(false)
{
}

Speech::~Speech()
{
    if (ctx) {
        whisper_free(ctx);
    }
}

bool Speech::init()
{
    Logger::log("[Whisper] Initialization started");
    if (isInitialized)
        return true;

    Logger::log("Loading whisper model...");

    // Initialize context params properly
    struct whisper_context_params cparams = {
        .use_gpu = true, // enable GPU if available
    };

    // Correct initialization with context params
    ctx = whisper_init_from_file_with_params("../../lib/whisper.cpp/models/ggml-model-whisper-base.en.bin", cparams);

    if (ctx == nullptr) {
        Logger::log("[Whisper] Critical error: Model load failed");
        return false;
    }

    Logger::log("[Whisper] Model loaded - Parameters: " + std::to_string(whisper_model_n_vocab(ctx)) + " vocab entries");
    isInitialized = true;
    return true;
}

void Speech::startRecording()
{
    std::lock_guard<std::mutex> lock(m_mutex);

    int err = snd_pcm_open(&capture_handle, "default", SND_PCM_STREAM_CAPTURE, 0);
    if (err < 0) {
        Logger::log("ALSA open error: " + std::string(snd_strerror(err)));
        return;
    }

    err = snd_pcm_set_params(capture_handle,
        SND_PCM_FORMAT_FLOAT_LE,
        SND_PCM_ACCESS_RW_INTERLEAVED,
        1, // Mono audio
        16000, // 16kHz sample rate
        1, // Allow software resampling
        500000); // 0.5 second buffer latency

    if (err < 0) {
        Logger::log("ALSA params error: " + std::string(snd_strerror(err)));
        snd_pcm_close(capture_handle);
        capture_handle = nullptr;
        return;
    }

    m_is_recording = true;
    audio_thread = std::thread(&Speech::processAudio, this);
    Logger::log("Audio: ALSA initialized successfully");
}

void Speech::processAudio()
{
    const int frames = 1024;
    std::vector<float> buffer(frames);

    while (m_is_recording) {
        if (!capture_handle) {
            Logger::log("Audio: PCM handle is null!");
            break;
        }

        int err = snd_pcm_readi(capture_handle, buffer.data(), frames);
        if (err == -EPIPE) {
            Logger::log("Audio: Overrun occurred");
            snd_pcm_prepare(capture_handle);
        } else if (err < 0) {
            Logger::log("Audio: Read error: " + std::string(snd_strerror(err)));
            break;
        }

        if (err > 0) {
            std::lock_guard<std::mutex> lock(m_mutex);
            audio_buffer.insert(audio_buffer.end(), buffer.begin(), buffer.begin() + err);
        }
    }

    if (capture_handle) {
        snd_pcm_close(capture_handle);
        capture_handle = nullptr;
    }
}

std::string Speech::transcribe_buffer()
{
    if (!ctx || audio_buffer.empty())
        return "";

    // Actual Whisper transcription implementation
    whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    wparams.print_realtime = false;
    wparams.print_progress = false;
    wparams.print_timestamps = false;
    wparams.print_special = false;
    wparams.translate = false;
    wparams.language = "en";
    wparams.n_threads = 4;

    if (whisper_full(ctx, wparams, audio_buffer.data(), audio_buffer.size()) != 0) {
        Logger::log("Error: Failed to process audio");
        return "";
    }

    std::string result;
    const int n_segments = whisper_full_n_segments(ctx);
    for (int i = 0; i < n_segments; ++i) {
        result += whisper_full_get_segment_text(ctx, i);
    }

    audio_buffer.clear();
    Logger::log("[Audio] Final buffer size before transcription: " + std::to_string(audio_buffer.size()) + " samples");
    return result;
}

void Speech::stopRecording()
{
    m_is_recording = false;

    if (audio_thread.joinable()) {
        audio_thread.join(); // Wait for processAudio to finish
    }

    // Remove the dangerous drain/drop calls - processAudio already cleans up
    Logger::log("[Audio] Recording stopped");

    // NEW: Final buffer processing
    if (!audio_buffer.empty()) {
        Logger::log("[Audio] Final buffer size: " + std::to_string(audio_buffer.size()));
    } else {
        Logger::log("[Audio] Warning: Empty audio buffer on stop");
    }
}

std::string Speech::transcribe(const std::string& audioFile)
{
    Logger::log("[Whisper] File transcription started: " + audioFile);
    std::vector<float> pcmf32;
    if (!::read_wav(audioFile, pcmf32)) {
        Logger::log("Error: Failed to read WAV file");
        return "";
    }

    // Use existing buffer transcription logic
    audio_buffer = pcmf32;
    return transcribe_buffer();
}