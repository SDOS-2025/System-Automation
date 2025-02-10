# System Automation using LLM Models

## Sponsor
**Startup Track**

## Development Team
- **Kushagra Gupta** - [kushagra22309@iiitd.ac.in](mailto:kushagra22309@iiitd.ac.in)
- **Rayyan Hussain** - [rayyan22399@iiitd.ac.in](mailto:rayyan22399@iiitd.ac.in)
- **Mehul Pahuja** - [mehul22295@iiid.ac.in](mailto:mehul22295@iiid.ac.in)
- **Aaradhya Verma** - [aaradhya22004@iiitd.ac.in](mailto:aaradhya22004@iiitd.ac.in)

## Introduction
The **System Automation using LLM Models** project aims to streamline and automate routine system tasks using Large Language Models (LLMs). The objective is to develop an intelligent automation system capable of executing user commands efficiently, reducing manual intervention, and improving productivity.

### Key Features
- **Automated Execution**: Perform system operations such as opening/closing applications, managing files, and handling processes without manual effort.
- **Voice & Text-based Automation**: Enable users to interact with the system using voice or text commands.
- **Browser Automation**: Perform common browser tasks such as opening tabs, navigating history, and handling downloads/uploads.
- **System Administration & Productivity Tasks**: Manage system settings, send emails, schedule events, and automate routine administrative tasks.

## Functional Requirements
### System-Level Automation
- Audio speed recognition for user input.
- Automate user inputs without manual intervention.
- Automate routine tasks and basic system operations.
- File handling and management.
- Process management.
- Opening and closing applications.
- System administration (e.g., changing settings, managing users).
- Taking screenshots.
- Productivity enhancements (e.g., sending mail, creating events/reminders).

### Browser Automation
- Launch new tabs and open specific websites.
- Navigate browser history (forward and back).
- Download and upload files.
- Web scraping and content summarization.
- Form automation (auto-filling data, submitting forms).

## Non-Functional Requirements
### User Interface Requirements
- **Intuitive UI/UX**: The system should have a minimalistic and easy-to-use interface.
- **Voice & Text Input Support**: Users should be able to give commands via text or voice.
- **Cross-Platform Compatibility**: The software should work on major operating systems (Windows, macOS, Linux).

### Performance Requirements
- **Low Latency Execution**: Commands should be executed with minimal delay.
- **Efficient Resource Utilization**: The system should operate efficiently without excessive CPU/memory usage.
- **Scalability**: The system should support additional automation tasks without significant performance degradation.

### Design Constraints
- **Tech Stack**:
  - Programming Language: Python
  - Frameworks: OpenAI/DeepSeek LLM APIs, PyAutoGUI (for system automation), Selenium (for browser automation), SpeechRecognition (for voice input)
  - Database: SQLite / PostgreSQL (if needed for task history/logs)
- **Security Considerations**:
  - User authentication and authorization for critical tasks.
  - Prevent unintended execution of harmful commands.
  - Secure API handling and access control.

## Further Details
- Each feature will be detailed with specific use cases in the documentation.
- Step-by-step implementation guides and tutorials will be available in the `docs/` directory.
- Future improvements will include integrating more complex AI-driven automation features.

## Installation
```sh
# Clone the repository
git clone https://github.com/your-repo/system-automation-llm.git
cd system-automation-llm
sudo apt-get install libgtkmm-3.0-dev libsqlite3-dev
cd Src/GUI
make all
```

