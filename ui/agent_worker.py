"""
Worker thread for handling agent interactions
"""
from PyQt6.QtCore import QThread, pyqtSignal

class AgentWorker(QThread):
    """Worker thread for agent interactions
    
    This worker thread handles the processing of user commands by either:
    1. Delegating to the orchestrator for processing
    2. Providing a mock response if no orchestrator is available
    
    Signals:
        update_signal: Emitted when UI should be updated with new messages
        error_signal: Emitted when an error occurs
        status_signal: Emitted when status changes
        task_signal: Emitted when a task status changes
    """
    update_signal = pyqtSignal(list, list)  # (messages, tasks)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    task_signal = pyqtSignal(str)
    
    def __init__(self, user_input, state, vision_agent=None, orchestrator=None):
        """Initialize the worker thread
        
        Args:
            user_input: The user's command text
            state: Application state dictionary 
            vision_agent: Optional vision agent for screen analysis
            orchestrator: Optional orchestrator for command processing
        """
        super().__init__()
        self.user_input = user_input
        self.state = state
        self.vision_agent = vision_agent
        self.orchestrator = orchestrator
        
    def run(self):
        """Run the worker thread - processes the user command"""
        try:
            # Add user message to chat (already done by controller, but kept for compatibility)
            self.state["messages"].append({
                "role": "user",
                "content": self.user_input
            })
            
            # Update UI with user message
            self.update_signal.emit(
                self.state["messages"],
                []  # Empty tasks list since we removed task functionality
            )
            
            # Process with orchestrator if available
            if self.orchestrator:
                # Use the orchestrator to process the text command
                self.orchestrator.process_text_command(self.user_input)
            else:
                # Simplified mock response for testing without orchestrator
                mock_response = "This is a simulated response. The orchestrator is not connected."
                
                # Add assistant message
                self.state["messages"].append({
                    "role": "assistant",
                    "content": mock_response
                })
                
                # Update UI
                self.update_signal.emit(
                    self.state["messages"],
                    []  # Empty tasks list
                )
                    
        except Exception as e:
            error_msg = str(e)
            self.error_signal.emit(error_msg)
            
        finally:
            self.state["stop"] = False 