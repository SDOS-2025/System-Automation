#include "../src/GUI/Speech.hpp"
#include <chrono> // For sleep duration
#include <filesystem> // For checking file existence
#include <gtest/gtest.h>
#include <thread> // For sleep

// Test fixture for Speech tests
class SpeechTest : public ::testing::Test {
protected:
    Speech speech_processor; // Instance of the class under test

    // Per-test set-up
    void SetUp() override
    {
        // Initialization code for each test, if needed.
        // Note: Tests requiring the Whisper model might depend on the model file path
        // being accessible relative to the test execution directory.
    }

    // Per-test tear-down
    void TearDown() override
    {
        // Cleanup code after each test.
        // Ensure recording is stopped if a test leaves it running.
        if (speech_processor.isRecording()) {
            speech_processor.stopRecording();
        }
    }

    // Helper to check if the model file seems accessible
    // Adjust path based on where tests are run relative to the project root
    bool modelFileExists()
    {
        // Path relative to src/GUI/Speech.cpp: "../../lib/whisper.cpp/models/ggml-model-whisper-base.en.bin"
        // Common execution path might be build/ or tests/
        // Adjust this path based on your build setup and execution location.
        // Example assuming execution from project root:
        return std::filesystem::exists("lib/whisper.cpp/models/ggml-model-whisper-base.en.bin");
        // Example assuming execution from build/ directory sibling to lib/:
        // return std::filesystem::exists("../lib/whisper.cpp/models/ggml-model-whisper-base.en.bin");
    }
};

// Test the constructor and initial state
TEST_F(SpeechTest, Constructor)
{
    ASSERT_FALSE(speech_processor.isRecording());
    // Add more initial state checks if needed
}

// Test the init() method
TEST_F(SpeechTest, Initialization)
{
    // This test requires the model file to be present and accessible.
    if (!modelFileExists()) {
        GTEST_SKIP() << "Whisper model file not found at expected location relative to test execution, skipping Initialization test.";
    }
    ASSERT_TRUE(speech_processor.init());
    // Could check internal state if needed, but prefer public interface tests.
}

// Test starting recording changes state.
// Note: This interacts with ALSA and may require a suitable environment.
TEST_F(SpeechTest, StartRecordingChangesState)
{
    ASSERT_FALSE(speech_processor.isRecording());
    speech_processor.startRecording();
    // Brief pause to allow thread startup (basic check)
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    ASSERT_TRUE(speech_processor.isRecording());
    // Clean up state for subsequent tests
    speech_processor.stopRecording();
}

// Test stopping recording changes state.
// Note: Interacts with ALSA.
TEST_F(SpeechTest, StopRecordingChangesState)
{
    // Arrange
    speech_processor.startRecording();
    std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Ensure started
    ASSERT_TRUE(speech_processor.isRecording());

    // Act
    speech_processor.stopRecording();

    // Assert
    ASSERT_FALSE(speech_processor.isRecording());
}

// Test transcribing an empty buffer (requires initialized context)
TEST_F(SpeechTest, TranscribeEmptyBuffer)
{
    if (!modelFileExists()) {
        GTEST_SKIP() << "Whisper model file not found, skipping TranscribeEmptyBuffer test.";
    }
    ASSERT_TRUE(speech_processor.init()); // Context needed

    std::string result = speech_processor.transcribe_buffer();
    ASSERT_EQ(result, ""); // Expect empty string for empty buffer
}

// Placeholder test for transcribing a WAV file
// TODO: Provide the path to a real WAV file and its expected transcription text.
TEST_F(SpeechTest, TranscribeWavFile_Placeholder)
{
    if (!modelFileExists()) {
        GTEST_SKIP() << "Whisper model file not found, skipping TranscribeWavFile test.";
    }
    ASSERT_TRUE(speech_processor.init()); // Context needed

    std::string testWavPath = "./test.wav"; // <<< --- CHANGE THIS to your test file path
    std::string expectedText = "Expected text here"; // <<< --- CHANGE THIS to expected transcription

    if (!std::filesystem::exists(testWavPath)) {
        GTEST_SKIP() << "Test WAV file not found at '" << testWavPath << "', skipping test.";
    }

    std::string result = speech_processor.transcribe(testWavPath);

    // Uncomment the assertion below when you have the file and expected text
    // ASSERT_EQ(result, expectedText);

    // Temporary check: ensure transcription produced some output
    ASSERT_FALSE(result.empty()) << "Transcription returned empty string for file: " << testWavPath;
    std::cout << "[ INFO ] Transcription result for " << testWavPath << ": " << result << std::endl; // Optional: print result for manual check
}

// Consider adding tests for:
// - Error handling (e.g., invalid ALSA device, model load failure if not skipped)
// - Behavior with actual recorded audio in transcribe_buffer() (requires feeding the buffer)
// - Thread safety if multiple threads interact with the Speech object.