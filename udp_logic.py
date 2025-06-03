import navigation as NAV, udp_sender as UDP, time, gui, threading, yolo, drone_feed, re  # import modules for nav logic, UDP comms, timing, and GUI

DELAY = 0.5  # seconds to wait between successive UDP commands
FLIP_DELAY = 1

STREAMING = False  # flag to indicate if video stream is active, to prevent multiple threads from starting it (it crashes if started twice)
# Note: The UDP_sender module is assumed to handle the socket connection and command sending.

INITIALIZED = False # flag to indicate if the UDP (command, streamon) connection has been initialized, to prevent re-initialization and making the drone misbehave.

'''Check if current position is within given tolerances of target.'''
def is_close_enough(current, target, x_tol=100, y_tol=50):
    """
    Args:
        current (tuple): Current (x, y) position
        target (tuple): Desired (x, y) position
        x_tol (int): Maximum horizontal tolerance
        y_tol (int): Maximum vertical tolerance
    Returns:
        bool: True if position within tolerances, else False
    """
    if current is None or target is None:
        return False  # missing either current or target data

    dx = abs(current[0] - target[0])  # horizontal distance
    dy = abs(current[1] - target[1])  # vertical distance

    return dx <= x_tol and dy <= y_tol  # within both tolerances

'''Send a Tello UDP command if its value exceeds thresholds.'''
def send_command_if_needed(cmd, skip_threshold=5, min_value=20):
    """
    Args:
        cmd (str): Command string in format '<direction> <value>'
        skip_threshold (int): Values <= this are ignored
        min_value (int): Smallest value to send if above skip_threshold
    """
    direction, value_str = cmd.split()  # split into action and amount
    value = int(value_str)  # convert amount to integer

    if value <= skip_threshold:
        print(f"Skipping small movement: {cmd}")  # ignore negligible adjustments
        return

    if value < min_value:
        value = min_value  # enforce minimum movement
    cmd_to_send = f"{direction} {value}"  # reconstruct command

    print(f"[UDP] Sending: {cmd_to_send}")  # debug output
    UDP.send_command(cmd_to_send)  # transmit over UDP
    time.sleep(DELAY)  # enforce pacing between commands

'''Calculate and send moves to approach a single waypoint.'''
def move_to_destination(dest):
    """
    Args:
        dest (tuple): Target (x, y) pixel coordinates
    Returns:
        bool: True if destination reached, else False
    """
    time.sleep(DELAY)  # brief pause before computing

    loc = yolo.drone_location  # read latest position
    if loc is None:
        print("[UDP] No vision data; skipping move.")  # cannot navigate without a fix
        return False

    # Step 1: compute forward/backward and sideways adjustments
    fwd_cmd, side_cmd = NAV.calculate_from_pixels(loc, dest)  # initial commands
    print(f"[UDP] 1. Calculated cmds: {fwd_cmd}, {side_cmd}")  # report for debugging
    send_command_if_needed(fwd_cmd)  # send forward/backward

    # Step 2: recompute and send lateral adjustment
    loc = yolo.drone_location  # get updated position
    _, side_cmd = NAV.calculate_from_pixels(loc, dest)  # adjust sideways only
    print(f"[UDP] 2. Sideways cmd: {side_cmd}")  # log lateral move
    send_command_if_needed(side_cmd)  # send sideways

    # Step 3: verify if within tolerance
    final_loc = yolo.drone_location  # final position after moves
    reached = is_close_enough(final_loc, dest, x_tol=128, y_tol=72)  # check arrival
    print(f"[UDP] Final {final_loc}, reached={reached}")  # summary
    return reached

'''Attempt moves up to a maximum retry count.'''
def retry_to_reach(dest, max_retries=3):
    """
    Args:
        dest (tuple): Target (x, y) pixel coordinates
        max_retries (int): Number of attempts before giving up
    """
    for attempt in range(1, max_retries + 1):
        if move_to_destination(dest):
            print(f"[UDP] Destination {dest} reached.")  # success message
            return
        print(f"[UDP] Retry {attempt}/{max_retries} for {dest}")  # log retry
    print(f"[UDP] Failed to reach {dest} after {max_retries} attempts.")  # final failure

'''Go through all waypoints defined in GUI list.'''
def execute_mission():
    """
    Returns:
        tuple or None: Last waypoint reached, or None if list empty
    """
    last = None  # track last successful destination
    for dest in gui.destination_list:  # iterate waypoints
        retry_to_reach(dest)  # perform movement with retries
        last = dest  # update last attempted
    return last  # return last processed waypoint

def initialize_and_start_stream():
    """
    Open the UDP socket, enter SDK mode, turn on the video stream,
    and launch the camera‐feed thread as soon as 'streamon' returns 'ok'.
    """

    global INITIALIZED, STREAMING  # access global flags

    if INITIALIZED:
        return  # already initialized, skip setup
    else:
        INITIALIZED = True # mark as initialized

    UDP.connect()                # open UDP socket
    time.sleep(DELAY)            # allow socket to settle

    # enter SDK mode
    response = UDP.send_command('command')
    if response == 'ok':
        print('[UDP] Entered SDK mode.')
    else:
        print('[UDP] Failed to enter SDK mode, retrying...')
        response = UDP.send_command('command')

    # request video stream
    response = UDP.send_command('streamon')
    if response == 'ok':
        # start the feed thread immediately
        global STREAMING  # access global flag
        if STREAMING != True:
            threading.Thread(target=drone_feed.run, daemon=True).start()
            STREAMING = True  # set streaming flag

        print('[UDP] Stream started successfully.')
        time.sleep(DELAY)       # brief settling wait
    else:
        print('[UDP] Stream start failed. Retrying...')
        response = UDP.send_command('streamon')

'''Wait until GUI destination list is populated.'''
def wait_for_mission():
    """
    Blocks until gui.destination_list is non-empty.
    """
    print("[UDP] Awaiting destination list...")  # idle state
    while not gui.destination_list:  # busy-wait until GUI populates list
        time.sleep(DELAY)  # reduce CPU usage

'''Perform drone takeoff sequence.'''
def takeoff_sequence():
    """
    Sends the necessary commands to prepare and take off.
    """
    print("[UDP] Mission start sequence")  # beginning mission
    for cmd in ('takeoff', 'up 150'):  # prep commands
        UDP.send_tello(cmd)  # send each prep command withot retrying
        time.sleep(DELAY)  # pause after each

    resp = UDP.send_command('tof?')

    # Extract the first number from the drone's response (e.g. "2156mm") using regex.
    # Handles None or bad responses safely by searching in an empty string if needed.
    # Try to extract the first (and only) run of digits
    m = re.search(r'(\d+)', resp or "")
    if not m:
        print(f"[UDP] Bad response to 'tof?': {resp!r}")
        return

    h_mm = int(m.group(1))

    # now only succeed if we're at least 2000 mm off the ground
    if h_mm >= 2000:
        print(f"[UDP] Takeoff ok, {h_mm} mm")
    else:
        print(f"[UDP] Takeoff failed, {h_mm} mm – ascending")
        takeoff_sequence()  # retry takeoff if too low


'''Wait for initial vision fix.'''
def wait_for_vision_fix():
    """
    Blocks until drone_location is set by vision thread.
    """
    print("[UDP] Waiting for vision fix...")  # prompt
    while yolo.drone_location is None:  # spin until vision thread updates
        time.sleep(0.1)  # short wait to avoid tight loop
    print(f"[UDP] First fix: {yolo.drone_location}")  # log initial position

'''Report battery level and final drone location.'''
def report_status():
    """
    Queries battery and prints the final position.
    """
    bat = UDP.send_command('battery?')  # query battery
    print(f"[UDP] Battery: {bat}")  # battery status
    print(f"[UDP] Final drone_location: {yolo.drone_location}")  # position report

'''Land the drone and cleanup UDP socket and GUI.'''
def land_and_cleanup():
    """
    Sends land command, closes socket, and clears GUI list.
    """
    global INITIALIZED
    time.sleep(DELAY)  # wait before landing
    UDP.send_command('land')  # land command
    time.sleep(DELAY)  # wait for land completion
    gui.destination_list.clear()  # reset for next mission


def flip_drone():
    """
    Sends flip command to the drone.
    """
    print("[UDP] Flipping drone...")  # flip prompt

    for cmd in ("f", "b", "l", "r"):  # perform all 4 flips

        time.sleep(FLIP_DELAY)
        UDP.send_command(f'flip {cmd}')  # flip forward

    print("[UDP] Flips complete.")  # confirmation message

'''Main UDP logic loop triggering missions.'''
def run():
    print("[UDP] UDP logic thread running...")  # startup notice
    while True:  # continuous operation
        wait_for_mission()  # block until destinations provided
        initialize_and_start_stream()  # ensure UDP and stream active
        takeoff_sequence()  # lift off
        wait_for_vision_fix()  # get first location fix
        execute_mission()  # fly through all waypoints
        report_status()  # battery and location
        flip_drone()  # optional flip command #uncomment to enable flips
        land_and_cleanup()  # land and reset GUI
