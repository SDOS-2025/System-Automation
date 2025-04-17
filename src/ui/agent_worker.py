"""
Worker thread for handling agent interactions
"""
from PyQt6.QtCore import QThread, pyqtSignal
from auto_control.loop import sampling_loop_sync

class AgentWorker(QThread):
    """Worker thread for agent interactions"""
    update_signal = pyqtSignal(list, list)  # (messages, tasks)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    task_signal = pyqtSignal(str)
    
    def __init__(self, user_input, state, vision_agent):
        super().__init__()
        self.user_input = user_input
        self.state = state
        self.vision_agent = vision_agent
        
    def run(self):
        """Run the worker thread"""
        try:
            # Validate API key
            if not self.state.get("api_key"):
                raise ValueError("API key is not set. Please configure it in settings.")
                
            # Add user message to chat
            self.state["messages"].append({
                "role": "user",
                "content": self.user_input
            })
            
            # Update UI with user message
            self.update_signal.emit(
                self.state["messages"],
                []  # Empty tasks list since we removed task functionality
            )
            
            # Create iterator for sampling loop
            loop_iterator = sampling_loop_sync(
                messages=self.state["messages"],
                vision_agent=self.vision_agent,
                screen_region=self.state.get("screen_region"),
                api_key=self.state["api_key"],
                base_url=self.state["base_url"],
                model=self.state["model"]
            )
            
            # Process responses
            for response in loop_iterator:
                if self.state.get("stop", False):
                    break
                    
                if response:
                    # Add assistant message
                    self.state["messages"].append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Update UI
                    self.update_signal.emit(
                        self.state["messages"],
                        []  # Empty tasks list
                    )
                    
        except Exception as e:
            error_msg = str(e)
            if "Illegal header value" in error_msg:
                error_msg = "Invalid API key. Please check your API key in settings."
            self.error_signal.emit(error_msg)
            
        finally:
            self.state["stop"] = False 