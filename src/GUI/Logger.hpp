#pragma once
#include <gtkmm.h>
#include <iostream>
#include <string>

class Logger {
private:
    inline static Gtk::TextView* logView = nullptr;
    inline static bool consoleEnabled = false;

public:
    static void init(Gtk::TextView* view, bool enableConsole = false)
    {
        logView = view;
        consoleEnabled = enableConsole;
    }

    static void log(const std::string& message)
    {
        // Always log to console
        std::cout << "[LOG] " << message << std::endl;

        // UI output remains conditional
        if (logView) {
            auto textBuffer = logView->get_buffer();
            textBuffer->insert(textBuffer->end(), message + "\n");
            auto endIter = textBuffer->end();
            logView->scroll_to(endIter);
        }

        // Force flush for immediate visibility
        std::cout << std::flush;
    }
};