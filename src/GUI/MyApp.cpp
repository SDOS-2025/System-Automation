#include "AppDB.cpp"
#include "Logger.hpp"
#include "Speech.hpp"
#include <bits/stdc++.h>
#include <gtkmm.h>
using namespace std;

class MyApp : public Gtk::Window {

private:
    AppDB myDb;
    int presetID;
    Speech speech;

    Gtk::Notebook notebook;

    Gtk::Box tab1Container;
    Gtk::Button mic; // Button widget
    Gtk::Label micDefaultText;

    Gtk::Box tab2Container;
    std::vector<Gtk::Label> history;

    Gtk::Box tab3Container;
    Gtk::Label apiKeyText;
    Gtk::Entry apiEntry;
    Gtk::Label sensitivityText;
    Gtk::Scale sensitivitySlider;
    Gtk::Button save;
    Gtk::Button clearHistory;
    Gtk::Button clearPresets;

    Gtk::Box tab4Container;
    Gtk::Box tab4Box1;
    Gtk::Entry name;
    Gtk::Entry command;
    Gtk::Button addButton;
    Gtk::Box tab4Box2;

    Gtk::TextView logView;
    Gtk::ScrolledWindow logScroll;

protected:
    void tab3OnSave()
    {
        string apiKey = apiEntry.get_text();
        float sensVal = static_cast<float>(sensitivitySlider.get_value());
        if (apiKey.size() > 0)
            myDb.updateSettings(apiKey, sensVal);
        else
            myDb.updateSettings(sensVal);
    }
    /*// Label widget
    Gtk::Entry m_entry;          // Entry (text box) widget
    Gtk::ComboBoxText m_combo_box; // ComboBox widget
    Gtk::CheckButton m_check_button; // CheckButton widget
    Gtk::RadioButton m_radio_button1; // RadioButton widget
    Gtk::RadioButton m_radio_button2; // RadioButton widget
    Gtk::RadioButton::Group m_radio_button_group; // Group for radio buttons
    Gtk::Scale m_slider;         // Slider widget
    Gtk::Image m_image;          // Image widget
    Gtk::SpinButton m_spin_button; // SpinButton widget
    Gtk::ProgressBar m_progress_bar; // ProgressBar widget
    Gtk::FileChooserButton m_file_chooser; // FileChooserButton widget
    */

    void tab4OnAdd()
    {
        string nameEntry = name.get_text();
        string commandEntry = command.get_text();
        if (nameEntry.size() > 0 && commandEntry.size() > 0)
            myDb.updatePresets(nameEntry, commandEntry);

        Gtk::Box* currPresetRow = Gtk::manage(new Gtk::Box);
        currPresetRow->set_orientation(Gtk::ORIENTATION_HORIZONTAL);
        currPresetRow->set_spacing(10);

        Gtk::Label* currID = Gtk::manage(new Gtk::Label);
        currID->set_text(to_string(presetID));
        Gtk::Label* currName = Gtk::manage(new Gtk::Label);
        currName->set_text(nameEntry);
        Gtk::Label* currCommand = Gtk::manage(new Gtk::Label);
        currCommand->set_text(commandEntry);

        currPresetRow->pack_start(*currID);
        currPresetRow->pack_start(*currName);
        currPresetRow->pack_start(*currCommand);

        tab4Box2.pack_start(*currPresetRow);
        presetID += 1;

        name.set_text("");
        command.set_text("");
        show_all_children();
        return;
    }

public:
    MyApp()
    {
        // creating database
        set_title("System Automation");
        set_default_size(1270, 720);
        notebook.set_tab_pos(Gtk::POS_TOP);
        //---------------------------
        tab1Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
        tab1Container.set_spacing(10);

        mic.set_label("Mic");
        micDefaultText.set_text("Start Listening...");

        tab1Container.pack_start(mic);
        tab1Container.pack_start(micDefaultText);

        // Setup logging
        logScroll.set_policy(Gtk::POLICY_AUTOMATIC, Gtk::POLICY_AUTOMATIC);
        logScroll.add(logView);
        logView.set_editable(false);
        logView.set_wrap_mode(Gtk::WRAP_WORD);
        Logger::init(&logView);

        // Add log view to tab1 (or wherever you want it)
        tab1Container.pack_start(logScroll);

        notebook.append_page(tab1Container, "Speak");

        //--------------------
        tab2Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
        tab2Container.set_spacing(10);

        // fetch the history and put it into the vector
        // then load
        notebook.append_page(tab2Container, "History");
        //---------------------------------------
        tab3Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
        tab3Container.set_spacing(10);

        // load default settings to
        apiKeyText.set_text("ChatGPT API Key:");
        apiEntry.set_placeholder_text(myDb.fetchSettingsAPI());
        sensitivityText.set_text("Sensitivity:");
        save.set_label("Save");
        save.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab3OnSave));
        sensitivitySlider.set_range(0, 1);
        sensitivitySlider.set_value(myDb.fetchSettingsSens());
        clearHistory.set_label("Clear History");
        clearPresets.set_label("Clear Presets");

        tab3Container.pack_start(apiKeyText);
        tab3Container.pack_start(apiEntry);
        tab3Container.pack_start(sensitivityText);
        tab3Container.pack_start(sensitivitySlider);
        tab3Container.pack_start(save);
        tab3Container.pack_start(clearHistory);
        tab3Container.pack_start(clearPresets);

        notebook.append_page(tab3Container, "Settings");
        //-----------------------------------------
        tab4Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
        tab4Container.set_spacing(10);

        tab4Box1.set_orientation(Gtk::ORIENTATION_HORIZONTAL);
        name.set_placeholder_text("Preset Name");
        tab4Box1.pack_start(name);
        command.set_placeholder_text("Input");
        tab4Box1.pack_start(command);
        addButton.set_label("+");
        addButton.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab4OnAdd));
        tab4Box1.pack_start(addButton);

        tab4Container.pack_start(tab4Box1);
        // load all the presets in the database, dump it in the vector;
        vector<vector<string>> fetchPresetsResults = myDb.fetchPresets();
        for (size_t i = 0; i < fetchPresetsResults.size(); i++) {
            cout << fetchPresetsResults[i][0] << " " << fetchPresetsResults[i][1] << " " << fetchPresetsResults[i][2] << endl;
        }

        tab4Box2.set_orientation(Gtk::ORIENTATION_VERTICAL);
        tab4Box2.set_spacing(10);
        presetID = fetchPresetsResults.size();
        for (size_t i = 0; i < fetchPresetsResults.size(); i++) {
            // create a box
            Gtk::Box* currPresetRow = Gtk::manage(new Gtk::Box);
            currPresetRow->set_orientation(Gtk::ORIENTATION_HORIZONTAL);
            currPresetRow->set_spacing(10);

            Gtk::Label* currID = Gtk::manage(new Gtk::Label);
            currID->set_text(fetchPresetsResults[i][0]);
            Gtk::Label* currName = Gtk::manage(new Gtk::Label);
            currName->set_text(fetchPresetsResults[i][1]);
            Gtk::Label* currCommand = Gtk::manage(new Gtk::Label);
            currCommand->set_text(fetchPresetsResults[i][2]);

            currPresetRow->pack_start(*currID);
            currPresetRow->pack_start(*currName);
            currPresetRow->pack_start(*currCommand);

            tab4Box2.pack_start(*currPresetRow);
        }
        tab4Container.pack_start(tab4Box2);
        // then add those labels;

        notebook.append_page(tab4Container, "Presets");
        //-----------------------------------------
        add(notebook);
        show_all_children();

        // Temporary test code
        if (speech.init()) {
            std::string result = speech.transcribe("test.wav");
            std::cout << "Transcription test: " << result << std::endl;
            Logger::log("Test transcription: " + result);
        }
    }

protected:
    void onMicClicked()
    {
        Logger::log("Initializing speech recognition...");
        if (speech.init()) {
            Logger::log("Processing audio file...");
            std::string result = speech.transcribe("test.wav");
            Logger::log("Transcription result: " + result);
            micDefaultText.set_text(result);
        } else {
            Logger::log("Failed to initialize speech recognition");
        }
    }
};

int main(int argc, char* argv[])
{
    // Initialize GTKmm
    Gtk::Main kit(argc, argv);

    // Create window instance
    MyApp sysAuto;

    // Run the main GTKmm loop
    Gtk::Main::run(sysAuto);

    return 0;
}
