import tkinter as tk  # Import tkinter module as tk for GUI elements
from tkinter import Button  # Import Button widget directly

# Virtual canvas dimensions (logical units)
VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 1920, 1080  # Set logical width and height

# Grid settings
GRID_SIZE = 50              # Distance between grid lines in logical units
GRID_COLOR = "gray"         # Color of grid lines

# Route drawing settings
ROUTE_COLOR_VERT = "green"   # Color for vertical segments of the route
ROUTE_COLOR_HORIZ = "blue"   # Color for horizontal segments of the route
ROUTE_DASH = (2, 2)           # Dash pattern for horizontal lines
LINE_WIDTH = 25               # Thickness of route lines

# Waypoint marker settings
WAYPOINT_COLOR = "red"       # Color of waypoint circles
WAYPOINT_RADIUS = 35          # Radius of waypoint markers in pixels
TEXT_COLOR = "black"         # Color of waypoint label text
TEXT_FONT = ("Arial", 15, "bold")  # Font for waypoint labels

# Constraints for adding waypoints
MIN_DELTA_X = 256             # Min horizontal distance between successive waypoints
MIN_DELTA_Y = 144             # Min vertical distance between successive waypoints
MIN_ALLOWED_AXIS_DELTA = 5    # Min movement along an axis to count as intentional
MIN_EDGE_MARGIN = 150         # Margin from edges where clicks are ignored

# State variables
waypoints = []        # Recorded logical coordinates of waypoints list
recording = False     # Flag indicating whether click recording is active
destination_list = [] # Final list of waypoints for the drone to follow

# GUI objects (initialized later)
root = tk.Tk()        # Create main Tkinter window
canvas = None         # Placeholder for Canvas widget reference
rec_btn = None        # Placeholder for record button reference
scale_x = 1.0         # Scaling factor in X direction (screen/logical)
scale_y = 1.0         # Scaling factor in Y direction (screen/logical)

def draw_grid():  # Function to draw the background grid
    canvas.delete("grid")  # Remove any existing grid lines
    # Draw vertical lines
    for x in range(0, VIRTUAL_WIDTH, GRID_SIZE):  # Iterate logical X positions
        sx = x * scale_x  # Convert logical X to screen X
        canvas.create_line(sx, 0, sx, VIRTUAL_HEIGHT * scale_y,  # Draw vertical line
                           fill=GRID_COLOR, tags="grid")  # Set color and tag
    # Draw horizontal lines
    for y in range(0, VIRTUAL_HEIGHT, GRID_SIZE):  # Iterate logical Y positions
        sy = y * scale_y  # Convert logical Y to screen Y
        canvas.create_line(0, sy, VIRTUAL_WIDTH * scale_x, sy,  # Draw horizontal line
                           fill=GRID_COLOR, tags="grid")  # Set color and tag

def draw_waypoints():  # Function to draw waypoints and connecting route
    canvas.delete("route")  # Clear previous route drawings

    # Draw connecting lines between waypoints
    for i in range(1, len(waypoints)):  # Iterate pairs of waypoints
        x0, y0 = waypoints[i - 1]  # Starting waypoint
        x1, y1 = waypoints[i]      # Ending waypoint

        # Convert logical coords to screen coords (invert Y axis)
        draw_x0 = x0 * scale_x  # Screen X for start
        draw_y0 = (VIRTUAL_HEIGHT - y0) * scale_y  # Screen Y for start
        draw_x1 = x1 * scale_x  # Screen X for end
        draw_y1 = (VIRTUAL_HEIGHT - y1) * scale_y  # Screen Y for end

        # Horizontal segment first: dashed blue
        canvas.create_line(
            draw_x0, draw_y0, draw_x1, draw_y0,  # Draw horizontal line segment
            fill=ROUTE_COLOR_HORIZ, dash=ROUTE_DASH,  # Set dash pattern
            width=LINE_WIDTH, tags="route"  # Set thickness and tag
        )
        # Vertical segment next: solid green
        canvas.create_line(
            draw_x1, draw_y0, draw_x1, draw_y1,  # Draw vertical line segment
            fill=ROUTE_COLOR_VERT, width=LINE_WIDTH,  # Set color and thickness
            tags="route"  # Tag for clearing later
        )

    # Draw waypoint markers and labels
    for i, (x, y) in enumerate(waypoints):  # Iterate each waypoint with index
        draw_x = x * scale_x  # Screen X for marker
        draw_y = (VIRTUAL_HEIGHT - y) * scale_y  # Screen Y for marker

        # Circle for the waypoint
        canvas.create_oval(
            draw_x - WAYPOINT_RADIUS, draw_y - WAYPOINT_RADIUS,  # Top-left of circle
            draw_x + WAYPOINT_RADIUS, draw_y + WAYPOINT_RADIUS,  # Bottom-right
            fill=WAYPOINT_COLOR, tags="route"  # Set fill and tag
        )
        # Number label inside the circle
        canvas.create_text(
            draw_x, draw_y,  # Position for text
            text=str(i + 1), fill=TEXT_COLOR,  # Label number and color
            font=TEXT_FONT, tags="route"  # Font and tag
        )

def on_click(event):  # Mouse click handler
    if not recording:  # Ignore clicks if not recording
        return

    # Convert screen coords back to logical coords
    x = event.x / scale_x  # Logical X coordinate
    y = VIRTUAL_HEIGHT - (event.y / scale_y)  # Logical Y coordinate, inverted

    # Ignore clicks too close to edges
    if (x < MIN_EDGE_MARGIN or x > VIRTUAL_WIDTH - MIN_EDGE_MARGIN or
        y < MIN_EDGE_MARGIN or y > VIRTUAL_HEIGHT - MIN_EDGE_MARGIN):  # Check margins
        return  # Skip if outside allowed area

    # If this is the first waypoint, just add it
    if not waypoints:  # No waypoints yet
        waypoints.append((x, y))  # Record first waypoint
        draw_waypoints()  # Update display
        return

    last_x, last_y = waypoints[-1]  # Previous waypoint coords
    dx = abs(x - last_x)  # Horizontal delta
    dy = abs(y - last_y)  # Vertical delta

    # Enforce minimum movement constraints
    if (dx < MIN_DELTA_X and dx >= MIN_ALLOWED_AXIS_DELTA and dy >= MIN_DELTA_Y) or \
       (dy < MIN_DELTA_Y and dy >= MIN_ALLOWED_AXIS_DELTA and dx >= MIN_DELTA_X):
        pass  # Allow intentional small movement on one axis
    elif dx < MIN_DELTA_X and dy < MIN_DELTA_Y:  # Too small movement overall
        return  # Ignore click

    # Record the valid waypoint and redraw
    waypoints.append((x, y))  # Add new waypoint to list
    draw_waypoints()  # Refresh route display

def toggle_rec():  # Toggle recording on/off
    global recording, waypoints, destination_list  # Modify globals
    if not recording:  # If currently not recording
        recording = True  # Start recording
        rec_btn.config(text="CLEAR")  # Change button label
    else:
        recording = False  # Stop recording
        rec_btn.config(text="REC")  # Reset button label
        # Reset recorded data
        waypoints.clear()  # Remove all waypoints
        destination_list.clear()  # Clear final list
        canvas.delete("route")  # Clear route visuals

def start_drone():  # START button action
    global destination_list  # Modify global list
    destination_list.clear()  # Clear previous destinations
    destination_list.extend(waypoints)  # Copy current waypoints
    print("Start pressed - saved waypoints to destination_list:", destination_list)  # Debug output

def stop_drone():  # STOP button action
    print("Stop pressed")  # Debug output
    import sys  # Import sys to exit
    sys.exit(0)  # Exit application

def configure_root_window(screen_width, screen_height):  # Window setup
    root.title("Drone Overlay")  # Set window title
    root.geometry(f"{screen_width}x{screen_height}+0+0")  # Fullscreen geometry
    root.configure(bg='white')  # Background color
    root.wm_attributes('-alpha', 0.5)       # Semi-transparent window
    root.wm_attributes('-topmost', True)    # Always stay on top
    root.overrideredirect(True)            # Remove borders

def create_canvas(screen_width, screen_height):  # Create drawing canvas
    global canvas  # Assign to global variable
    canvas_frame = tk.Frame(root)  # Frame to hold canvas
    canvas_frame.pack(fill="both", expand=True)  # Expand to available space

    canvas = tk.Canvas(
        canvas_frame,
        width=screen_width,  # Pixel width
        height=screen_height - 60,  # Leave space for buttons
        bg='white', highlightthickness=0  # No border highlight
    )
    canvas.pack(fill="both", expand=True)  # Fill entire frame

def create_buttons():  # Create REC, START, STOP buttons
    global rec_btn  # Access rec_btn global
    btn_frame = tk.Frame(root, bg='white')  # Frame for buttons
    btn_frame.pack(fill='x', side='bottom')  # Dock to bottom

    rec_btn = Button(btn_frame, text="REC", width=10, command=toggle_rec)  # Record button
    rec_btn.pack(side='left', padx=5, pady=5)  # Position with padding

    Button(btn_frame, text="START", width=10, command=start_drone).pack(side='left', padx=5)  # Start
    Button(btn_frame, text="STOP", width=10, command=stop_drone).pack(side='left', padx=5)  # Stop

def initialize_screen_scaling():  # Calculate scaling factors
    global scale_x, scale_y  # Modify globals
    screen_width = root.winfo_screenwidth()  # Get actual screen width
    screen_height = root.winfo_screenheight()  # Get actual screen height
    scale_x = screen_width / VIRTUAL_WIDTH  # Compute X scale
    scale_y = screen_height / VIRTUAL_HEIGHT  # Compute Y scale
    return screen_width, screen_height  # Return dimensions

def initialize_gui():  # Full GUI initialization
    screen_width, screen_height = initialize_screen_scaling()  # Setup scaling
    configure_root_window(screen_width, screen_height)  # Window props
    create_canvas(screen_width, screen_height)  # Canvas setup
    create_buttons()  # Add controls
    canvas.bind("<Button-1>", on_click)  # Bind mouse clicks
    draw_grid()  # Initial grid draw

def run():  # Main entry point
    initialize_gui()  # Init interface
    root.mainloop()  # Start Tk event loop

if __name__ == "__main__":  # If script is run directly
    run()  # Launch application
