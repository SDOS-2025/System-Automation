#include <gtkmm.h>
#include <bits/stdc++.h>
#include "AppDB.cpp"
using namespace std;

class MyApp : public Gtk::Window {

    private:
        AppDB myDb;
        int presetID;

        Gtk::Notebook notebook;

        Gtk::Box tab1Container;
        Gtk::Button mic;        // Button widget
        Gtk::Label micDefaultText;

        Gtk::Box tab2Container;
        std::vector<Gtk:: Label> history;

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

    protected:
        void tab3OnSave(){
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

        void tab4OnAdd(){
            string nameEntry = name.get_text();
            string commandEntry = command.get_text();
            if(nameEntry.size() > 0 && commandEntry.size() > 0){
                try{
                    myDb.updatePresets(nameEntry, commandEntry);
                    Gtk::Box* currPresetRow = Gtk::manage(new Gtk::Box);
                    currPresetRow -> set_orientation(Gtk::ORIENTATION_HORIZONTAL);
                    currPresetRow -> set_spacing(10);

                    Gtk::Label* currID = Gtk::manage(new Gtk::Label);
                    currID -> set_text(to_string(presetID));
                    Gtk::Label* currName = Gtk::manage(new Gtk::Label);
                    currName->set_text(nameEntry);
                    Gtk::Label* currCommand = Gtk::manage(new Gtk::Label);
                    currCommand -> set_text(commandEntry);

                    currPresetRow -> pack_start(*currID);
                    currPresetRow -> pack_start(*currName);
                    currPresetRow -> pack_start(*currCommand);

                    tab4Box2.pack_start(*currPresetRow);
                    presetID += 1;

                    name.set_text("");
                    command.set_text("");
                    show_all_children();
                    return;
                }
                catch(...){
                    cout << "the preset name shoudl be unique" << endl;
                    Gtk::MessageDialog dialog(*this, "Alert", false, Gtk::MESSAGE_ERROR, Gtk::BUTTONS_OK, true);
                    dialog.set_secondary_text("Preset names should be unique!");
                    dialog.run();
                }
            }
       }

        void tab3OnClear1(){
            myDb.clearPresets();
            Gtk::Widget* box = &tab4Box2;
            tab4Container.remove(tab4Box2);
            tab4Box2 = Gtk::Box();
            tab4Box2.set_orientation(Gtk::ORIENTATION_VERTICAL);
            tab4Box2.set_spacing(10);
            tab4Container.pack_start(tab4Box2);
            show_all_children();
        }
    public:
        MyApp() {
            //creating database
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

            notebook.append_page(tab1Container, "Speak");

            //--------------------
            tab2Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
            tab2Container.set_spacing(10);

            //fetch the history and put it into the vector
            //then load
            notebook.append_page(tab2Container, "History");
            //---------------------------------------
            tab3Container.set_orientation(Gtk::ORIENTATION_VERTICAL);
            tab3Container.set_spacing(10);

            //load default settings to        
            apiKeyText.set_text("ChatGPT API Key:");
            apiEntry.set_placeholder_text(myDb.fetchSettingsAPI());
            sensitivityText.set_text("Sensitivity:");
            save.set_label("Save");
            save.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab3OnSave));
            sensitivitySlider.set_range(0, 1);
            sensitivitySlider.set_value(myDb.fetchSettingsSens());
            clearHistory.set_label("Clear History");
            clearPresets.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab3OnClear1));
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
            //load all the presets in the database, dump it in the vector;
            vector<vector<string>> fetchPresetsResults = myDb.fetchPresets();
            for(int i = 0; i < fetchPresetsResults.size(); i++){
                cout << fetchPresetsResults[i][0] << " " << fetchPresetsResults[i][1] << " " << fetchPresetsResults[i][2] << endl;
            }

            tab4Box2.set_orientation(Gtk::ORIENTATION_VERTICAL);
            tab4Box2.set_spacing(10);
            presetID = fetchPresetsResults.size();
            for(int i = 0; i < fetchPresetsResults.size(); i++){
                //create a box
                Gtk::Box* currPresetRow = Gtk::manage(new Gtk::Box);
                currPresetRow -> set_orientation(Gtk::ORIENTATION_HORIZONTAL);
                currPresetRow -> set_spacing(10);

                Gtk::Label* currID = Gtk::manage(new Gtk::Label);
                currID -> set_text(fetchPresetsResults[i][0]);
                Gtk::Label* currName = Gtk::manage(new Gtk::Label);
                currName->set_text(fetchPresetsResults[i][1]);
                Gtk::Label* currCommand = Gtk::manage(new Gtk::Label);
                currCommand -> set_text(fetchPresetsResults[i][2]);

                currPresetRow -> pack_start(*currID);
                currPresetRow -> pack_start(*currName);
                currPresetRow -> pack_start(*currCommand);

                tab4Box2.pack_start(*currPresetRow);
            }
            tab4Container.pack_start(tab4Box2);
            //then add those labels;
            

            notebook.append_page(tab4Container, "Presets");
            //-----------------------------------------
            add(notebook);
            show_all_children();
            /*
            // Button widget
            m_button.signal_clicked().connect(sigc::mem_fun(*this, &MyWindow::on_button_clicked));

            // Entry widget (text box)
            m_entry.set_placeholder_text("Type something...");

            // ComboBox widget
            m_combo_box.append("Option 1");
            m_combo_box.append("Option 2");
            m_combo_box.append("Option 3");
            m_combo_box.set_active(0); // Set default option

            // CheckButton widget
            m_check_button.set_label("Enable feature");

            // Create radio button group
            m_radio_button_group = Gtk::RadioButton::Group();

            // Assign radio buttons to the group
            m_radio_button1.set_group(m_radio_button_group);
            m_radio_button2.set_group(m_radio_button_group);

            // Slider (Scale) widget
            m_slider.set_range(0, 5987);
            m_slider.set_increments(1, 300);
            m_slider.signal_value_changed().connect(sigc::mem_fun(*this, &MyWindow::on_slider_changed));

            // Image widget (using a sample image)
            m_image.set("sample_image.png");

            // SpinButton widget (for numeric input)
            m_spin_button.set_range(0, 100);
            m_spin_button.set_increments(1, 10);

            // ProgressBar widget
            m_progress_bar.set_fraction(0.5); // Set it to 50%

            // FileChooserButton widget (for selecting a file)
            m_file_chooser.set_action(Gtk::FILE_CHOOSER_ACTION_OPEN);
            m_file_chooser.set_title("Choose a file");

            m_box.pack_start(m_combo_box);
            m_box.pack_start(m_check_button);
            m_box.pack_start(m_radio_button1);
            m_box.pack_start(m_radio_button2);
            m_box.pack_start(m_slider);
            m_box.pack_start(m_image);
            m_box.pack_start(m_spin_button);
            m_box.pack_start(m_progress_bar);
            m_box.pack_start(m_file_chooser);
            */
        }

};

int main(int argc, char *argv[]) {
    // Initialize GTKmm
    Gtk::Main kit(argc, argv);

    // Create window instance
    MyApp sysAuto;

    // Run the main GTKmm loop
    Gtk::Main::run(sysAuto);

    return 0;
}
