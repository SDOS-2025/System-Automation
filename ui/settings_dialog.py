"""
Settings dialog for application configuration
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                          QLabel, QLineEdit, QPushButton, QCheckBox)

class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.state = state
        self.parent_window = parent
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Model settings
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_input = QLineEdit(self.state["model"])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        
        # Base URL settings
        url_layout = QHBoxLayout()
        url_label = QLabel("Base URL:")
        self.base_url_input = QLineEdit(self.state["base_url"])
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.base_url_input)
        
        # API key settings
        api_layout = QHBoxLayout()
        api_label = QLabel("API Key:")
        self.api_key_input = QLineEdit(self.state["api_key"])
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        
        # Voice input settings
        voice_layout = QHBoxLayout()
        self.auto_submit_checkbox = QCheckBox("Auto-submit voice transcription")
        self.auto_submit_checkbox.setChecked(self.state.get("auto_submit_voice", False))
        voice_layout.addWidget(self.auto_submit_checkbox)
        
        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all elements to main layout with some spacing
        layout.addSpacing(15)
        layout.addLayout(model_layout)
        layout.addSpacing(15)
        layout.addLayout(url_layout)
        layout.addSpacing(15)
        layout.addLayout(api_layout)
        layout.addSpacing(15)
        layout.addLayout(voice_layout)
        layout.addSpacing(25)
        layout.addLayout(button_layout)
        layout.addSpacing(15)
    
    def get_settings(self):
        """Get settings content"""
        return {
            "model": self.model_input.text(),
            "base_url": self.base_url_input.text(),
            "api_key": self.api_key_input.text(),
            "auto_submit_voice": self.auto_submit_checkbox.isChecked()
        } 