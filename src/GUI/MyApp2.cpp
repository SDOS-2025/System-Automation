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
        vector<Gtk::FlowBox*> presetsVector;

        void applyCSS(){
            auto provider = Gtk::CssProvider::create();
            provider->load_from_path("style.css");

            auto display = Gdk::Display::get_default();
            Gtk::StyleContext::add_provider_for_display(display, provider, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
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

                micButton.set_label("Mic");
                micButton.set_name("mic");
                micButton.set_size_request(200, -1);

                micTranscription.set_wrap_mode(Gtk::WrapMode::WORD);  // Enable word wrapping
                micTranscription.set_name("stt");
                micTranscription.set_editable(false);  // Make it read-only
                micTranscription.get_buffer()->set_text("Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!Zqxvbnm asdfghjkl poiuytrewq 9876543210! Blarg snoof wibbly-wobbly timey-wimey flux capacitor engaged. Quantum banana paradox disrupts entropy flow, causing a recursive causality loop. Meanwhile, the cosmic spaghetti monster debates Schrödinger’s cat over simulated universes. Frobnicate the doohickey before the gizmo implodes!."); 
                micTextWindow.set_child(micTranscription);
                micTextWindow.set_size_request(600, -1);  // Preferred width (400px), height (-1 means default)

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
                tab3Box1.set_size_request(-1, 100);
                tab3Box1.set_margin_start(100); 
                tab3Box1.append(nameField);
                tab3Box1.append(commandField);
                tab3Box1.append(addButton);
                tab3Container.append(tab3Box1);

                //fetching db 
                presetsWindow.set_size_request(-1, 400);
                presetsList.set_selection_mode(Gtk::SelectionMode::NONE);
                vector<vector<string>> fetchPresetsResults = myDb.fetchPresets();
                for(int i = 0; i < fetchPresetsResults.size(); i++){
                    cout << fetchPresetsResults[i][0] << " " << fetchPresetsResults[i][1] << " " << fetchPresetsResults[i][2] << endl;
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
                    currRow -> append(*currNo);
                    currRow -> append(*currName);
                    currRow -> append(*currCommand);
                    currRow -> set_selection_mode(Gtk::SelectionMode::NONE);
                    currRow -> set_margin_start(50);
                    presetsVector.push_back(currRow);
                    presetsList.append(*currRow);
                } 
                presetsWindow.set_child(presetsList);
                tab3Container.append(presetsWindow);

                notebook.append_page(tab3Container, "Presets");
                //---------------------------------
                applyCSS();
                set_child(notebook);
        }
};

int main(int argc, char *argv[]) {
    auto app = Gtk::Application::create("com.example.systemautomation");
    return app->make_window_and_run<MyApp>(argc, argv); //template function
}