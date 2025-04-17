"""
Main application window
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit,
                           QMessageBox, QDialog, QSystemTrayIcon)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QPixmap, QIcon, QTextCursor, QTextCharFormat, QColor

from xbrain.utils.config import Config
from auto_control.agent.vision_agent import VisionAgent
from util.download_weights import OMNI_PARSER_DIR

from ui.theme import apply_theme, THEMES
from ui.settings_dialog import SettingsDialog
from ui.agent_worker import AgentWorker
from ui.tray_icon import StatusTrayIcon

# Intro text for application
INTRO_TEXT = '''
Your intelligent desktop assistant
'''

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, args):
        super().__init__()
        self.args = args
        
        # Initialize state
        self.state = self.setup_initial_state()
        
        # Initialize Agent
        self.vision_agent = VisionAgent(
            yolo_model_path=os.path.join(OMNI_PARSER_DIR, "icon_detect", "model.pt")
        )
        
        # Setup UI and tray icon
        self.setup_tray_icon()
        self.setWindowTitle("General AI Agent")
        self.setMinimumSize(900, 600)  # Reduced minimum size
        self.init_ui()
        self.apply_theme()
        
        print("\n\n🚀 PyQt6 application launched")
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        try:
            script_dir = Path(__file__).parent
            image_path = script_dir.parent / "imgs" / "logo.png"
            pixmap = QPixmap(str(image_path))
            icon_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            app_icon = QIcon(icon_pixmap)
            self.setWindowIcon(app_icon)
            
            self.tray_icon = StatusTrayIcon(app_icon, self)
            self.tray_icon.show()
        except Exception as e:
            print(f"Error setting up tray icon: {e}")
            self.tray_icon = None
    
    def setup_initial_state(self):
        """Set up initial state"""
        config = Config()
        return {
            "api_key": config.OPENAI_API_KEY or "",
            "base_url": config.OPENAI_BASE_URL or "https://api.openai.com/v1",
            "model": config.OPENAI_MODEL or "gpt-4o",
            "theme": "Dark",  # Set dark theme as default
            "messages": [],
            "chatbox_messages": [],
            "auth_validated": False,
            "responses": {},
            "tools": {},
            "only_n_most_recent_images": 2,
            "stop": False
        }
    
    def apply_theme(self):
        """Apply the current theme to the application"""
        apply_theme(self, self.state.get("theme", "Light"))
    
    def init_ui(self):
        """Initialize UI components"""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Add margins
        main_layout.setSpacing(15)  # Add spacing between elements
        
        # Header section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        title_label = QLabel("General AI Agent")
        title_label.setObjectName("title_label")  # Set object name for custom styling
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(24)
        font.setWeight(600)  # Make it bold
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        # Introduction text
        intro_label = QLabel(INTRO_TEXT)
        intro_label.setObjectName("intro_label")  # Set object name for custom styling
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_label.setWordWrap(True)
        font = intro_label.font()
        font.setPointSize(14)
        intro_label.setFont(font)
        header_layout.addWidget(intro_label)
        
        # Settings button and clear chat button
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.settings_button = QPushButton("Settings")
        self.clear_button = QPushButton("Clear Chat")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.clear_button.clicked.connect(self.clear_chat)
        
        buttons_layout.addWidget(self.settings_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        # Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(10)
        
        # Chat history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(200)  # Set minimum height
        self.chat_display.setMaximumHeight(400)  # Set maximum height
        chat_layout.addWidget(self.chat_display)
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.process_input)
        
        self.submit_button = QPushButton("Send")
        self.stop_button = QPushButton("Stop")
        self.submit_button.clicked.connect(self.process_input)
        self.stop_button.clicked.connect(self.stop_process)
        
        input_layout.addWidget(self.chat_input, 8)
        input_layout.addWidget(self.submit_button, 1)
        input_layout.addWidget(self.stop_button, 1)
        
        # Add all components to main layout
        main_layout.addWidget(header_widget)
        main_layout.addWidget(buttons_widget)
        main_layout.addWidget(chat_widget, 1)  # Chat area takes remaining space
        main_layout.addWidget(input_widget)
        
        self.setCentralWidget(central_widget)
    
    def open_settings_dialog(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.state)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Get and apply new settings
            settings = dialog.get_settings()
            
            self.state["model"] = settings["model"]
            self.state["base_url"] = settings["base_url"]
            self.state["api_key"] = settings["api_key"]
    
    def process_input(self):
        """Process user input"""
        user_input = self.chat_input.text()
        if not user_input.strip():
            return
            
        # Clear input box
        self.chat_input.clear()
        
        # Minimize main window
        self.showMinimized()
        
        # Create and start worker thread
        self.worker = AgentWorker(user_input, self.state, self.vision_agent)
        self.worker.update_signal.connect(self.update_ui)
        self.worker.error_signal.connect(self.handle_error)
        
        # Connect signals to tray icon if available
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.worker.status_signal.connect(self.tray_icon.update_status)
            self.worker.task_signal.connect(self.tray_icon.update_task)
        
        self.worker.start()
    
    def handle_error(self, error_message):
        """Handle error messages"""
        # Restore main window to show the error
        self.showNormal()
        self.activateWindow()
        
        # Show error message
        QMessageBox.warning(self, "Connection Error", 
                           f"Error connecting to AI service:\n{error_message}\n\nPlease check your network connection and API settings.")
    
    @pyqtSlot(list, list)
    def update_ui(self, chatbox_messages, tasks):
        """Update UI with new messages"""
        # Update chat display
        self.chat_display.clear()
        for msg in chatbox_messages:
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                # Format message based on role
                if role == "user":
                    self.chat_display.append(f"You: {content}")
                elif role == "assistant":
                    self.chat_display.append(f"AI: {content}")
            else:
                # If it's already a string, just append it
                self.chat_display.append(str(msg))
            
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
        
        # Store messages
        self.state["chatbox_messages"] = chatbox_messages
    
    def stop_process(self):
        """Stop processing - handles both button click and hotkey press"""
        self.state["stop"] = True
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.terminate()
        if self.isMinimized():
            self.showNormal()
            self.activateWindow()
        
        self.chat_display.append("<span style='color:red'>⚠️ Operation stopped by user</span>")
        self.register_stop_hotkey()
    
    def clear_chat(self):
        """Clear chat history"""
        self.state["messages"] = []
        self.state["chatbox_messages"] = []
        self.state["responses"] = {}
        self.state["tools"] = {}
        
        self.chat_display.clear()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon is not None and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        elif self.state.get("stop", False) and hasattr(self, 'worker') and self.worker is not None:
            self.state["stop"] = False
            event.ignore()
        elif hasattr(self, 'worker') and self.worker is not None and self.worker.isRunning():
            reply = QMessageBox.question(self, 'Exit Confirmation',
                                       '自动化任务仍在运行中，确定要退出程序吗？',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                keyboard.unhook_all()
                event.accept()
            else:
                event.ignore()
        else:
            keyboard.unhook_all()
            event.accept() 