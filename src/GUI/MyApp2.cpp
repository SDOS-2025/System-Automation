#include <gtkmm.h>
#include <bits/stdc++.h>
#include "AppDB.cpp"
using namespace std;

class MyApp : public Gtk::Window {
    private:
        AppDB myDb;
        int presetID;

        Gtk::Notebook notebook;

        Gtk::FlowBox tab1Container;
        Gtk::Button micButton;        // Button widget
        Gtk::ScrolledWindow micTextWindow;
        Gtk::TextView micTranscription;

        Gtk::FlowBox tab2Container;
        std::vector<Gtk:: Label> history; //each row would be a flow box?

        Gtk::ListBox tab3Container;
        Gtk::FlowBox tab3Box1;
        Gtk::Entry nameField;
        Gtk::Entry commandField;
        Gtk::Button addButton;
        Gtk::ListBox presetsList;
        Gtk::ScrolledWindow presetsWindow;
        vector<Gtk::ListBoxRow*> presetsVector;

        Gtk::ListBox tab4Container;
        Gtk::FlowBox tab4Box1;
        Gtk::Label apiLabel;
        Gtk::Entry apiEntry;
        Gtk::FlowBox tab4Box2;
        Gtk::Label sensLabel;
        Gtk::Scale sensSlider;
        Gtk::FlowBox tab4Box3;
        Gtk::Button clearHistory;
        Gtk::Button clearPresets;
        Gtk::Button save;

        void applyCSS(){
            auto provider = Gtk::CssProvider::create();
            provider->load_from_path("style.css");

            auto display = Gdk::Display::get_default();
            Gtk::StyleContext::add_provider_for_display(display, provider, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
        }

        void tab4OnSave(){
            string apiKey = apiEntry.get_text();
            float sensVal = static_cast<float>(sensSlider.get_value());
            if (apiKey.size() > 0)
                myDb.updateSettings(apiKey, sensVal);
            else
                myDb.updateSettings(sensVal);
        }
        
        void tab4OnClear1(){
            myDb.clearPresets();
            for(int i = 0; i < presetsVector.size(); i++){
                presetsList.remove(*presetsVector[i]);
            }          
            presetsVector.clear();
        }

        void tab3OnAdd(){
            string nameEntryVal = nameField.get_text();
            string commandEntryVal = commandField.get_text();
            if(nameEntryVal.size() > 0 && commandEntryVal.size() > 0){
                try{
                    myDb.updatePresets(nameEntryVal, commandEntryVal);
                    
                    Gtk::ListBoxRow* row = Gtk::manage(new Gtk::ListBoxRow);
                    Gtk::FlowBox* currRow = Gtk::manage(new Gtk::FlowBox);
                    Gtk::Label* currNo = Gtk::manage(new Gtk::Label);
                    Gtk::Label* currName = Gtk::manage(new Gtk::Label);
                    Gtk::TextView* currCommand = Gtk::manage(new Gtk::TextView);
                    currRow -> set_name("presetRows");
                    currRow -> set_size_request(-1, 70);
                    currNo -> set_text(to_string(presetID));
                    currNo -> set_size_request(40, -1);
                    currName -> set_text(nameEntryVal);
                    currName -> set_size_request(200, -1);
                    currCommand -> get_buffer() -> set_text(commandEntryVal);
                    currCommand -> set_size_request(400, -1);
                    currCommand -> set_justification(Gtk::Justification::CENTER);
                    currCommand -> set_wrap_mode(Gtk::WrapMode::WORD);
                    currRow -> append(*currNo);
                    currRow -> append(*currName);
                    currRow -> append(*currCommand);
                    currRow -> set_selection_mode(Gtk::SelectionMode::NONE);
                    currRow -> set_margin_start(50);

                    row -> set_child(*currRow);
                    presetsVector.push_back(row);
                    presetsList.append(*row);

                    presetID += 1;
                    return;
                }
                catch(...){
                    cout << "the preset name shoudl be unique" << endl;
                    auto dialog = std::make_shared<Gtk::MessageDialog>(*this, "Alert", false, 
                                    Gtk::MessageType::ERROR, Gtk::ButtonsType::OK, true);
                    dialog->set_secondary_text("Preset names should be unique!");
                    dialog->set_transient_for(*this);  // Attach to main window
                    dialog->set_modal(true);
                    dialog->signal_response().connect([dialog](int) {//dialog[3]
                        dialog->hide();  // Hide the dialog when a button is clicked
                    }); 
                    dialog->present();  // Show the dialog
                    // Show the dialog
                }
            }
        }
    public:
        MyApp() {

                auto settings = Gtk::Settings::get_default();
                settings->set_property("gtk-application-prefer-dark-theme", true);
                set_title("System Automation");
                set_default_size(850, 600);
                set_resizable(false);  
                notebook.set_tab_pos(Gtk::PositionType::TOP);

                //---------------------------
                tab1Container.set_name("tab1Container");
                tab1Container.set_margin_top(10);
                tab1Container.set_margin_bottom(10);
                tab1Container.set_column_spacing(10);
                tab1Container.set_margin_start(10);
                tab1Container.set_margin_end(10);
                tab1Container.set_selection_mode(Gtk::SelectionMode::NONE);

                micButton.set_label("Mic");
                micButton.set_name("mic");
                micButton.set_size_request(200, -1);

                micTranscription.set_wrap_mode(Gtk::WrapMode::WORD);  // Enable word wrapping
                micTranscription.set_name("stt");
                micTranscription.set_editable(false);  // Make it read-only
                micTranscription.get_buffer()->set_text("Speech To Text will appear here...."); 
                micTranscription.set_justification(Gtk::Justification::CENTER); 
                micTextWindow.set_child(micTranscription);
                micTextWindow.set_size_request(600, -1);  // Preferred width (400px), height (-1 means default)
                micTextWindow.set_margin_top(10);

                tab1Container.append(micButton);  // (col, row, width, height)
                tab1Container.append(micTextWindow);

                notebook.append_page(tab1Container, "Home");

                //-------------------------------
                tab2Container.set_name("tab2Container");
                tab2Container.set_margin_top(10);
                tab2Container.set_margin_bottom(10);
                tab2Container.set_column_spacing(10);
                tab2Container.set_margin_start(10);
                tab2Container.set_margin_end(10);

                notebook.append_page(tab2Container, "History");
                //---------------------------------
                tab3Container.set_name("tab3Container");
                tab3Container.set_margin_top(10);
                tab3Container.set_margin_bottom(10);
                tab3Container.set_margin_start(10);
                tab3Container.set_margin_end(10);
                tab3Container.set_selection_mode(Gtk::SelectionMode::NONE);

                nameField.set_placeholder_text("Preset Name");
                commandField.set_placeholder_text("Command");
                commandField.set_size_request(350, -1);
                addButton.set_label("+");
                addButton.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab3OnAdd));
                tab3Box1.set_size_request(-1, 100);
                tab3Box1.set_selection_mode(Gtk::SelectionMode::NONE);
                tab3Box1.set_margin_start(100); 
                tab3Box1.append(nameField);
                tab3Box1.append(commandField);
                tab3Box1.append(addButton);
                tab3Container.append(tab3Box1);

                //fetching db 
                presetsWindow.set_size_request(-1, 400);
                presetsList.set_selection_mode(Gtk::SelectionMode::NONE);
                vector<vector<string>> fetchPresetsResults = myDb.fetchPresets();
                presetID = fetchPresetsResults.size();
                for(int i = 0; i < fetchPresetsResults.size(); i++){
                    cout << fetchPresetsResults[i][0] << " " << fetchPresetsResults[i][1] << " " << fetchPresetsResults[i][2] << endl;
                    Gtk::ListBoxRow* row = Gtk::manage(new Gtk::ListBoxRow);
                    Gtk::FlowBox* currRow = Gtk::manage(new Gtk::FlowBox);
                    currRow -> set_name("presetRows");
                    currRow -> set_size_request(-1, 70);
                    Gtk::Label* currNo = Gtk::manage(new Gtk::Label);
                    Gtk::Label* currName = Gtk::manage(new Gtk::Label);
                    Gtk::TextView* currCommand = Gtk::manage(new Gtk::TextView);
                    currNo -> set_text(fetchPresetsResults[i][0]);
                    currNo -> set_size_request(40, -1);
                    currName -> set_text(fetchPresetsResults[i][1]);
                    currName -> set_size_request(200, -1);
                    currCommand -> get_buffer() -> set_text(fetchPresetsResults[i][2]);
                    currCommand -> set_size_request(400, -1);
                    currCommand -> set_wrap_mode(Gtk::WrapMode::WORD);
                    currCommand -> set_justification(Gtk::Justification::CENTER);
                    currRow -> append(*currNo);
                    currRow -> append(*currName);
                    currRow -> append(*currCommand);
                    currRow -> set_selection_mode(Gtk::SelectionMode::NONE);
                    currRow -> set_margin_start(50);

                    row -> set_child(*currRow);
                    presetsVector.push_back(row);
                    presetsList.append(*row);
                } 
                presetsWindow.set_child(presetsList);
                tab3Container.append(presetsWindow);
                notebook.append_page(tab3Container, "Presets");
                //---------------------------------
                tab4Container.set_selection_mode(Gtk::SelectionMode::NONE);
                tab4Container.set_margin_top(20);
                
                apiLabel.set_text("OpenAI API Key:");
                apiLabel.set_size_request(200, -1);
                apiEntry.set_placeholder_text(myDb.fetchSettingsAPI());
                apiEntry.set_size_request(600, -1);
                tab4Box1.append(apiLabel);
                tab4Box1.append(apiEntry);
                tab4Box1.set_size_request(-1, 100);
                tab4Box1.set_selection_mode(Gtk::SelectionMode::NONE);
                tab4Container.append(tab4Box1);

                sensLabel.set_text("Sensitivity:");
                sensLabel.set_size_request(200, -1);
                sensSlider.set_range(0, 1);
                sensSlider.set_size_request(600, 100);
                sensSlider.set_draw_value(true);   // Show value on the scale itself
                sensSlider.set_value(myDb.fetchSettingsSens());
                tab4Box2.append(sensLabel);
                tab4Box2.append(sensSlider);
                tab4Box2.set_size_request(-1, 100);
                tab4Box2.set_selection_mode(Gtk::SelectionMode::NONE);
                tab4Container.append(tab4Box2);

                clearHistory.set_label("Clear History");
                clearPresets.set_label("Clear Presets");
                clearPresets.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab4OnClear1));
                save.set_label("Save Changes");
                save.signal_clicked().connect(sigc::mem_fun(*this, &MyApp::tab4OnSave));
                tab4Box3.append(clearHistory);
                tab4Box3.append(clearPresets);
                tab4Box3.append(save);
                tab4Box3.set_size_request(-1, 50);
                tab4Box3.set_margin_start(20);
                tab4Box3.set_selection_mode(Gtk::SelectionMode::NONE);
                tab4Container.append(tab4Box3);

                notebook.append_page(tab4Container, "Settings");
                //--------------------------------
                applyCSS();
                set_child(notebook);
        }
};

int main(int argc, char *argv[]) {
    auto app = Gtk::Application::create("com.example.systemautomation");
    return app->make_window_and_run<MyApp>(argc, argv); //template function
}