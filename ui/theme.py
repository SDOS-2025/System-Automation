"""
Theme definitions and theme handling functionality
"""

# Theme definitions
THEMES = {
    "Light": {
        "main_bg": "#F8FAFC",
        "widget_bg": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#8B5CF6",
        "secondary_accent": "#EC4899",
        "tertiary_accent": "#10B981",
        "button_bg": "#E2E8F0",
        "button_text": "#1E293B",
        "border": "#CBD5E1",
        "selection_bg": "#8B5CF6",
        "hover_bg": "#CBD5E1",
        "error": "#EF4444",
        "success": "#10B981",
        "warning": "#F59E0B",
        "card_bg": "#FFFFFF",
        "input_bg": "#F1F5F9"
    },
    "Dark": {
        "main_bg": "#0A0A0F",  # Deeper dark background
        "widget_bg": "#12121A",  # Slightly lighter dark
        "text": "#E2F8FF",  # Bright cyan-white
        "accent": "#4A5B8C",  # Steel blue-gray
        "secondary_accent": "#566270",  # Subtle slate
        "tertiary_accent": "#3D4B66",  # Deep blue-gray
        "button_bg": "#12121A",
        "button_text": "#E2F8FF",
        "border": "#1F1F2C",
        "selection_bg": "#4A5B8C",
        "hover_bg": "#1F1F2C",
        "error": "#CF4B6C",  # Muted red
        "success": "#4B6B8C",  # Steel blue
        "warning": "#B3864F",  # Muted gold
        "card_bg": "#12121A",
        "input_bg": "#0A0A0F",
        "chat_bubble_bg": "#12121A",
        "chat_bubble_user": "#4A5B8C",
        "chat_text_user": "#FFFFFF",
        "glow": "#4A5B8C80"  # Semi-transparent steel blue for glow effects
    }
}

def apply_theme(widget, theme_name="Dark"):
    """Apply the specified theme to the widget"""
    theme = THEMES[theme_name]
    
    # Create stylesheet for the application
    stylesheet = f"""
    QMainWindow {{
        background-color: {theme['main_bg']};
        color: {theme['text']};
    }}
    
    QWidget {{
        background-color: {theme['main_bg']};
        color: {theme['text']};
    }}
    
    QLabel {{
        color: {theme['text']};
        font-size: 14px;
        font-weight: 400;
    }}
    
    QPushButton {{
        background-color: {theme['button_bg']};
        color: {theme['button_text']};
        border: 1px solid {theme['accent']};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 13px;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {theme['accent']};
        color: {theme['text']};
        border: 1px solid {theme['accent']};
    }}
    
    QPushButton:pressed {{
        background-color: {theme['secondary_accent']};
        color: {theme['text']};
        border: 1px solid {theme['secondary_accent']};
    }}
    
    QLineEdit {{
        background-color: {theme['input_bg']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        selection-background-color: {theme['selection_bg']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {theme['accent']};
        background-color: {theme['widget_bg']};
    }}
    
    QTextEdit {{
        background-color: {theme['widget_bg']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        selection-background-color: {theme['selection_bg']};
    }}
    
    QTextEdit:focus {{
        border: 2px solid {theme['accent']};
    }}
    
    /* Scrollbar styling */
    QScrollBar:vertical {{
        background-color: {theme['main_bg']};
        width: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {theme['accent']};
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {theme['tertiary_accent']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    /* Custom chat message styling */
    QTextEdit#chat_display {{
        padding: 16px;
        line-height: 1.5;
    }}
    
    /* Title label special styling */
    QLabel#title_label {{
        color: {theme['text']};  /* Changed to white */
        font-size: 24px;
        font-weight: 600;
        padding: 10px;
    }}
    
    /* Intro text special styling */
    QLabel#intro_label {{
        color: {theme['tertiary_accent']};
        font-size: 14px;
        font-weight: 400;
        padding: 5px;
    }}
    """
    
    widget.setStyleSheet(stylesheet) 