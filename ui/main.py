"""
Main entry point for System Automation application
"""
import sys
import argparse
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow  # Import restructured MainWindow class

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="System Automation")
    parser.add_argument("--windows_host_url", type=str, default='localhost:8006')
    parser.add_argument("--omniparser_server_url", type=str, default="localhost:8000")
    return parser.parse_args()

def run_ui(orchestrator=None):
    """Function that can be imported to run the UI with an orchestrator instance
    
    Args:
        orchestrator: Optional Orchestrator instance to connect UI signals to
        
    Returns:
        MainWindow instance
    """
    # Filter out arguments we don't handle like --gui
    filtered_args = [arg for arg in sys.argv if not arg.startswith('--gui')]
    sys.argv = filtered_args
    
    # Parse our own arguments
    args = parse_arguments()
    
    # Create window with orchestrator
    window = MainWindow(args, orchestrator_control=orchestrator)
    return window

def main():
    """Main application entry point when run directly"""
    args = parse_arguments()
    app = QApplication(sys.argv)
    window = MainWindow(args)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 