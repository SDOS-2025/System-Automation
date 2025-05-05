import tkinter as tk
from tkinter import Button
import sys
from typing import Optional, Tuple

class ScreenSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide the main window

        # Create a semi-transparent, topmost, fullscreen window
        self.window = tk.Toplevel(self.root)
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-alpha", 0.3) # Semi-transparent
        self.window.attributes("-topmost", True)

        # Initialize variables
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None
        self.current_x: Optional[float] = None
        self.current_y: Optional[float] = None
        self.selection_rect: Optional[int] = None
        self.confirm_button: Optional[Button] = None
        self.result: Optional[Tuple[int, int, int, int]] = None

        # Create canvas
        self.canvas = tk.Canvas(self.window, bg="gray20", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.window.bind("<Escape>", self.cancel)

    def on_press(self, event):
        # Clear existing selection/button
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        if self.confirm_button:
            self.confirm_button.destroy()
            self.confirm_button = None

        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        # Create rectangle for selection visualization
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=3 # Use a visible color
        )

    def on_drag(self, event):
        if self.start_x is None or self.start_y is None or self.selection_rect is None:
            return # Drag started without press?

        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)

        # Update selection rectangle coordinates
        self.canvas.coords(self.selection_rect,
                           self.start_x, self.start_y,
                           self.current_x, self.current_y)

        # (Optional) Update transparent overlay effect if desired
        # self.update_overlay_region()

    # def update_overlay_region(self):
    #     """ Creates an overlay effect where only the selected region is clear."""
    #     if self.start_x is None or self.start_y is None or self.current_x is None or self.current_y is None:
    #         return
    #     self.canvas.delete("transparent_region")
    #     x1 = min(self.start_x, self.current_x)
    #     y1 = min(self.start_y, self.current_y)
    #     x2 = max(self.start_x, self.current_x)
    #     y2 = max(self.start_y, self.current_y)
    #     # Draw grey overlay covering everything
    #     self.canvas.create_rectangle(
    #         0, 0, self.window.winfo_width(), self.window.winfo_height(),
    #         fill="gray20", outline="", tags="transparent_region"
    #     )
    #     # Punch a hole in the overlay for the selected region
    #     self.canvas.create_rectangle(
    #         x1, y1, x2, y2, fill="", outline="", tags="transparent_region"
    #     )
    #     # Ensure selection rectangle is visible on top
    #     if self.selection_rect:
    #          self.canvas.tag_raise(self.selection_rect)

    def on_release(self, event):
        if self.start_x is None or self.start_y is None or self.selection_rect is None:
            return # Released without press?

        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)

        # Check if selection is valid (minimum size)
        if abs(self.current_x - self.start_x) > 10 and abs(self.current_y - self.start_y) > 10:
            self.show_confirm_button()
        else:
             # If selection too small, reset
             self.canvas.delete(self.selection_rect)
             self.selection_rect = None
             self.start_x = self.start_y = None

    def show_confirm_button(self):
        if self.confirm_button:
            self.confirm_button.destroy()

        if self.start_x is None or self.start_y is None or self.current_x is None or self.current_y is None:
            return

        # Calculate coordinates of the selection bounds
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)

        # Determine button position (e.g., near the release point or a corner)
        # Simple approach: place below and right of the release point
        btn_x = self.current_x + 10
        btn_y = self.current_y + 10

        # Boundary checks (ensure button is within screen bounds)
        width, height = self.window.winfo_width(), self.window.winfo_height()
        btn_width_approx = 80
        btn_height_approx = 30
        if btn_x + btn_width_approx > width:
            btn_x = self.current_x - btn_width_approx - 10 # Move left
        if btn_y + btn_height_approx > height:
            btn_y = self.current_y - btn_height_approx - 10 # Move up
        btn_x = max(0, btn_x) # Ensure not off left edge
        btn_y = max(0, btn_y) # Ensure not off top edge


        # Create the button
        self.confirm_button = Button(
            self.window, text="Confirm", command=self.confirm,
            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), relief="flat",
            padx=5, pady=2
        )
        self.confirm_button.place(x=btn_x, y=btn_y)

    def confirm(self):
        if self.start_x is None or self.start_y is None or self.current_x is None or self.current_y is None:
            self.cancel()
            return

        # Get selection coordinates
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)

        self.result = (int(x1), int(y1), int(x2), int(y2))
        self.close_window()

    def cancel(self, event=None):
        self.result = None
        self.close_window()

    def close_window(self):
        """Safely destroys the tkinter windows."""
        if hasattr(self, 'window') and self.window.winfo_exists():
             self.window.destroy()
        if hasattr(self, 'root') and self.root.winfo_exists():
             self.root.quit() # Stops mainloop
             self.root.destroy()

    def get_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """Starts the selection process and returns the selected region or None."""
        self.root.mainloop()
        # Ensure window is destroyed even if mainloop exited prematurely
        self.close_window()
        return self.result


if __name__ == "__main__":
    print("Starting screen selector. Drag to select, press Esc to cancel.")
    selector = ScreenSelector()
    region = selector.get_selection()
    if region:
        print(f"Selected region: {region}")
    else:
        print("Selection cancelled.")
    sys.exit(0)
