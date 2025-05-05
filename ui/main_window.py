"""
Main application window - Follows MVC pattern with better component organization
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit,
                           QMessageBox, QDialog, QSystemTrayIcon)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QObject
from PyQt6.QtGui import QPixmap, QIcon, QTextCursor, QTextCharFormat, QColor

# Remove external dependencies that don't exist
# from xbrain.utils.config import Config
# from auto_control.agent.vision_agent import VisionAgent
# from util.download_weights import OMNI_PARSER_DIR

from ui.theme import apply_theme, THEMES
from ui.settings_dialog import SettingsDialog
from ui.agent_worker import AgentWorker
from ui.tray_icon import StatusTrayIcon

# Intro text for application
INTRO_TEXT = '''
Your intelligent system automation assistant
'''

class MainWindow(QMainWindow):
    """Main application window using MVC pattern"""
    
    # Define signals for controller communication
    command_initiated = pyqtSignal(str)  # Signal emitted when user initiates a command
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are changed
    
    def __init__(self, args, orchestrator_control=None):
        super().__init__()
        # Model - Data
        self.model = MainWindowModel()
        
        # Controller - Logic
        self.controller = MainWindowController(self.model, orchestrator_control)
        
        # Arguments from command line
        self.args = args
        
        # Setup UI components
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Initialize UI components - View part of MVC"""
        # Setup window properties
        self.setWindowTitle("System Automation")
        self.setMinimumSize(900, 600)
        
        # Setup tray icon
        self._setup_tray_icon()
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Add UI components
        main_layout.addWidget(self._create_header_section())
        main_layout.addWidget(self._create_buttons_section())
        main_layout.addWidget(self._create_chat_section(), 1)  # Chat takes remaining space
        main_layout.addWidget(self._create_input_section())
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Apply theme
        apply_theme(self, self.model.state.get("theme", "Dark"))
        
        print("\n\n🚀 PyQt6 application launched")
        
    def _create_header_section(self):
        """Create header section with title and intro text"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("System Automation")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(24)
        font.setWeight(600)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        # Introduction text
        intro_label = QLabel(INTRO_TEXT)
        intro_label.setObjectName("intro_label")
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_label.setWordWrap(True)
        font = intro_label.font()
        font.setPointSize(14)
        intro_label.setFont(font)
        header_layout.addWidget(intro_label)
        
        return header_widget
        
    def _create_buttons_section(self):
        """Create section with settings and clear buttons"""
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.settings_button = QPushButton("Settings")
        self.clear_button = QPushButton("Clear Chat")
        
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.clear_button.clicked.connect(self.controller.clear_chat)
        
        buttons_layout.addWidget(self.settings_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        return buttons_widget
        
    def _create_chat_section(self):
        """Create chat display section"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(10)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(200)
        self.chat_display.setMaximumHeight(400)
        self.chat_display.setObjectName("chat_display")
        chat_layout.addWidget(self.chat_display)
        
        return chat_widget
        
    def _create_input_section(self):
        """Create user input section"""
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # Input field
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.process_input)
        
        # Buttons
        self.submit_button = QPushButton("Send")
        self.stop_button = QPushButton("Stop")
        
        self.submit_button.clicked.connect(self.process_input)
        self.stop_button.clicked.connect(self.controller.stop_process)
        
        input_layout.addWidget(self.chat_input, 8)
        input_layout.addWidget(self.submit_button, 1)
        input_layout.addWidget(self.stop_button, 1)
        
        return input_widget
    
    def _setup_tray_icon(self):
        """Setup system tray icon"""
        try:
            # Use a default icon for the tray icon
            icon = QIcon.fromTheme("dialog-information")
            self.setWindowIcon(icon)
            
            self.tray_icon = StatusTrayIcon(icon, self)
            self.tray_icon.show()
            
            print("Tray icon set up successfully")
        except Exception as e:
            print(f"Error setting up tray icon: {e}")
            self.tray_icon = None
    
    def _connect_signals(self):
        """Connect signals between components"""
        # Connect to orchestrator if provided
        if self.controller.orchestrator:
            print("Connecting orchestrator signals")
            self.controller.orchestrator.log_signal.connect(self.controller.handle_log)
            self.controller.orchestrator.response_signal.connect(self.controller.handle_response)
            self.controller.orchestrator.error_signal.connect(self.controller.handle_error)
            self.controller.orchestrator.task_step_signal.connect(self.controller.handle_task_step)
            
        # Connect our signals to controller
        self.command_initiated.connect(self.controller.process_command)
        self.settings_changed.connect(self.controller.update_settings)
        
        # Connect model change notifications
        self.model.messages_changed.connect(self.update_chat_display)
        
    def process_input(self):
        """Process user input from UI"""
        user_input = self.chat_input.text()
        if not user_input.strip():
            return
            
        # Clear input box
        self.chat_input.clear()
        
        # Add to display
        self.controller.add_user_message(user_input)
        
        # Emit signal for processing
        self.command_initiated.emit(user_input)
        
        # Minimize window after sending
        self.showMinimized()
    
    def open_settings_dialog(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.model.state)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Get and emit settings
            settings = dialog.get_settings()
            self.settings_changed.emit(settings)
    
    def update_chat_display(self):
        """Update chat display with messages from model"""
        self.chat_display.clear()
        for msg in self.model.state.get("chatbox_messages", []):
            if isinstance(msg, dict):
                sender = msg.get("sender", "")
                message = msg.get("message", "")
                self.controller.format_and_add_message(self.chat_display, sender, message)
            
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon is not None and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        elif self.model.state.get("stop", False) and self.controller.worker is not None:
            self.model.state["stop"] = False
            event.ignore()
        elif hasattr(self.controller, 'worker') and self.controller.worker is not None and self.controller.worker.isRunning():
            reply = QMessageBox.question(self, 'Exit Confirmation',
                                       'Tasks are still running. Are you sure you want to exit?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class MainWindowModel(QObject):
    """Model component for storing application state"""
    
    # Signal when messages change
    messages_changed = pyqtSignal()
    
    def __init__(self):
        """Initialize model state"""
        super().__init__()
        self.state = {
            "api_key": "",  # These would come from config or env vars
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "theme": "Dark",  # Set dark theme as default
            "messages": [],
            "chatbox_messages": [],
            "auth_validated": False,
            "responses": {},
            "tools": {},
            "only_n_most_recent_images": 2,
            "stop": False
        }
        
    def add_message(self, sender, message):
        """Add a message to the chat history"""
        self.state["chatbox_messages"].append({"sender": sender, "message": message})
        
        # For API format messages
        if sender == "User":
            self.state["messages"].append({
                "role": "user",
                "content": message
            })
        elif sender == "Assistant":
            self.state["messages"].append({
                "role": "assistant",
                "content": message
            })
            
        # Emit signal that messages changed
        self.messages_changed.emit()
        
    def update_settings(self, settings):
        """Update settings in the model"""
        self.state.update(settings)
        
    def clear_messages(self):
        """Clear all messages"""
        self.state["messages"] = []
        self.state["chatbox_messages"] = []
        self.state["responses"] = {}
        self.state["tools"] = {}
        self.messages_changed.emit()


class MainWindowController:
    """Controller component handling business logic"""
    
    def __init__(self, model, orchestrator=None):
        """Initialize controller with model and orchestrator"""
        self.model = model
        self.orchestrator = orchestrator
        self.worker = None
        
    def process_command(self, command):
        """Process a command from the user"""
        # Create and start worker thread
        self.worker = AgentWorker(
            user_input=command, 
            state=self.model.state, 
            vision_agent=None,
            orchestrator=self.orchestrator
        )
        
        # Connect signals
        self.worker.update_signal.connect(self.update_ui)
        self.worker.error_signal.connect(self.handle_error)
        
        # Start processing
        self.worker.start()
        
    def add_user_message(self, message):
        """Add a user message to the model"""
        self.model.add_message("User", message)
        
    def handle_log(self, log_message):
        """Handle log messages from orchestrator"""
        self.model.add_message("System", log_message)
        
    def handle_response(self, response_text):
        """Handle responses from orchestrator"""
        self.model.add_message("Assistant", response_text)
        
    def handle_error(self, error_message):
        """Handle error messages"""
        # Show error message
        QMessageBox.warning(None, "Connection Error", 
                          f"Error connecting to AI service:\n{error_message}\n\nPlease check your network connection and API settings.")
    
    def update_ui(self, messages, tasks):
        """Update UI with new messages"""
        # This is called from the worker thread with new messages
        # We just need to refresh the view since the model is already updated
        self.model.messages_changed.emit()
    
    def stop_process(self):
        """Stop processing - handles both button click and hotkey press"""
        self.model.state["stop"] = True
        if self.worker is not None:
            self.worker.terminate()
            
        # Add message about stopping
        self.model.add_message("System", "⚠️ Operation stopped by user")
    
    def clear_chat(self):
        """Clear chat history"""
        self.model.clear_messages()
        
    def update_settings(self, settings):
        """Update settings in the model"""
        self.model.update_settings(settings)
        
    def handle_task_step(self, step_message):
        """Handle task step messages from orchestrator"""
        # Add as a special task step message type
        self.model.add_message("TaskStep", step_message)
    
    def format_and_add_message(self, text_edit, sender, message):
        """Format and add a message to the text edit widget"""
        # Format based on sender
        if sender == "User":
            color = "blue"
        elif sender == "Assistant":
            color = "green"
        elif sender == "System":
            color = "gray"
        elif sender == "TaskStep":
            color = "purple"  # Special color for task steps
        else:
            color = "black"
            
        # Create formatted text
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add sender with formatting
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        format.setFontWeight(700)  # Bold
        
        # Use specific prefix for different message types
        if sender == "TaskStep":
            # Don't show sender, just format the whole message as a task step
            cursor.insertText("➤ ", format)
        else:
            cursor.insertText(f"{sender}: ", format)
        
        # Add message with normal formatting
        format = QTextCharFormat()
        cursor.insertText(f"{message}\n\n", format)
        
        # Scroll to bottom
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible() 