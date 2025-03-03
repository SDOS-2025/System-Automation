#include "wav.h"
#include "Logger.hpp"
#include <fstream>
#include <vector>

bool read_wav(const std::string& fname, std::vector<float>& pcmf32)
{
    Logger::log("Reading WAV file: " + fname);

    std::ifstream fin(fname, std::ios::binary);
    if (!fin) {
        Logger::log("Error: Failed to open file");
        return false;
    }

    // Read RIFF header
    char riff[4];
    fin.read(riff, 4);
    if (std::string(riff, 4) != "RIFF") {
        Logger::log("Error: Not a RIFF file");
        fin.close();
        return false;
    }

    // Skip file size
    fin.seekg(4, std::ios_base::cur);

    // Read WAVE header
    char wave[4];
    fin.read(wave, 4);
    if (std::string(wave, 4) != "WAVE") {
        Logger::log("Error: Not a WAVE file");
        fin.close();
        return false;
    }

    // Find fmt chunk
    char fmt[4];
    fin.read(fmt, 4);
    if (std::string(fmt, 4) != "fmt ") {
        Logger::log("Error: Missing fmt chunk");
        fin.close();
        return false;
    }

    // Read fmt chunk size
    uint32_t fmtSize;
    fin.read(reinterpret_cast<char*>(&fmtSize), 4);

    // Read audio format (1 = PCM)
    uint16_t audioFormat;
    fin.read(reinterpret_cast<char*>(&audioFormat), 2);
    if (audioFormat != 1) {
        Logger::log("Error: Not PCM format (format=" + std::to_string(audioFormat) + ")");
        fin.close();
        return false;
    }

    // Read channels
    uint16_t channels;
    fin.read(reinterpret_cast<char*>(&channels), 2);
    if (channels < 1 || channels > 2) {
        Logger::log("Error: Only mono/stereo supported (channels=" + std::to_string(channels) + ")");
        fin.close();
        return false;
    }

    // Read sample rate
    uint32_t sampleRate;
    fin.read(reinterpret_cast<char*>(&sampleRate), 4);
    if (sampleRate != 16000) {
        Logger::log("Error: Expected 16kHz sample rate (got " + std::to_string(sampleRate) + " Hz)");
        fin.close();
        return false;
    }

    // Skip bytes per second and block align
    fin.seekg(6, std::ios_base::cur);

    // Read bits per sample
    uint16_t bitsPerSample;
    fin.read(reinterpret_cast<char*>(&bitsPerSample), 2);
    if (bitsPerSample != 16) {
        Logger::log("Error: Expected 16-bit samples (got " + std::to_string(bitsPerSample) + " bits)");
        fin.close();
        return false;
    }

    // Find data chunk with proper chunk skipping
    char chunkID[4];
    uint32_t chunkSize;
    bool foundData = false;

    while (true) {
        fin.read(chunkID, 4);
        if (fin.eof())
            break;

        fin.read(reinterpret_cast<char*>(&chunkSize), 4);

        if (std::string(chunkID, 4) == "data") {
            foundData = true;
            break;
        }

        // Skip unwanted chunks
        Logger::log("Skipping chunk: " + std::string(chunkID, 4) + " (" + std::to_string(chunkSize) + " bytes)");
        fin.seekg(chunkSize, std::ios_base::cur);
    }

    if (!foundData) {
        Logger::log("Error: Missing data chunk after searching all chunks");
        fin.close();
        return false;
    }

    // Read data size
    uint32_t dataSize;
    fin.read(reinterpret_cast<char*>(&dataSize), 4);

    // Handle malformed files that report 0 data size
    if (dataSize == 0) {
        // Calculate remaining file size
        const auto currentPos = fin.tellg();
        fin.seekg(0, std::ios::end);
        dataSize = static_cast<uint32_t>(fin.tellg() - currentPos);
        fin.seekg(currentPos);
        Logger::log("Computed data size from file remainder: " + std::to_string(dataSize));
    }

    // Read PCM data (handle mono/stereo)
    std::vector<int16_t> pcm16(dataSize / 2);
    fin.read(reinterpret_cast<char*>(pcm16.data()), dataSize);

    if (channels == 2) {
        // Convert stereo to mono by averaging channels
        Logger::log("Converting stereo to mono");
        std::vector<int16_t> mono(pcm16.size() / 2);
        for (size_t i = 0; i < mono.size(); i++) {
            mono[i] = static_cast<int16_t>((pcm16[2 * i] + pcm16[2 * i + 1]) / 2);
        }
        pcm16 = std::move(mono);
    }

    if (fin.gcount() != dataSize) {
        Logger::log("Error: Read " + std::to_string(fin.gcount()) + " bytes, expected " + std::to_string(dataSize));
        fin.close();
        return false;
    }

    // Convert to float32
    pcmf32.resize(pcm16.size());
    for (size_t i = 0; i < pcm16.size(); i++) {
        pcmf32[i] = static_cast<float>(pcm16[i]) / 32768.0f;
    }

    Logger::log("Successfully read " + std::to_string(pcmf32.size()) + " samples");
    fin.close();
    return true;
}