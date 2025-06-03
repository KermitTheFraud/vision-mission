# udp_sender.py

import socket

# ─── Tello and local configuration ───────────────────────────────────────────
TELLO_IP   = '192.168.10.1' # Tello drone's IP address
TELLO_PORT = 8889 # Port used by the Tello for command communication
LOCAL_IPS  = ['192.168.10.2', '192.168.10.3'] # sometimes the first one doesn't work
# ────────────────────────────────────────────────────────────────────────────
LOCAL_PORT = 9000 # Local port to bind for sending/receiving
TIMEOUT    = 15.0 # Seconds to wait for response from the drone, mustn't be longer than the drone's internal timeout

_sock = None # Global variable to hold the socket object

def connect():
    """Try each LOCAL_IP in turn until bind() succeeds."""
    global _sock
    _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Creates a UDP-socket AF.INET = IPV4, DGRAM = UDP.
    _sock.settimeout(TIMEOUT) # Set a timeout for receiving data 

    last_exc = None # Store last exception to raise if all bindings fail
    for ip in LOCAL_IPS:
        try:
            _sock.bind((ip, LOCAL_PORT)) # Attempt to bind socket to current IP and port
            print(f"Bound to {ip}:{LOCAL_PORT}")  # Success message
            return _sock  # Return the successfully bound socket
        except OSError as e:
            print(f"Could not bind to {ip}:{LOCAL_PORT} → {e}") # Log binding error
            last_exc = e # Save exception to raise later if needed

    raise last_exc  # Raise last exception if none of the IPs worked

def send_tello(cmd: str) -> str:
    """Send one SDK command and return the response (never blows up on bad bytes)."""
    if _sock is None:
        raise RuntimeError("Socket not connected: call connect() first") # Ensure socket is connected
    _sock.sendto(cmd.encode('utf-8'), (TELLO_IP, TELLO_PORT)) #Encodes the sent command to bytes with UTF-8.
    try:
        resp, _ = _sock.recvfrom(1024) # Wait for response (max 1024 bytes).
    except socket.timeout:
        return '(timeout)' # No response received within timeout period
    except ConnectionResetError:
        return '(connection reset)' # Connection was reset (e.g., drone rebooted)

    # Try UTF-8, fall back silently if there's invalid bytes
    try:
        text = resp.decode('utf-8') # Try decoding response as UTF-8
    except UnicodeDecodeError:
        text = resp.decode('utf-8', errors='ignore') # Ignore bad bytes if decoding fails
    return text.strip() #Returns the decoded bytes as a text string.

def send_command(command: str) -> str:
    """Send + print, retrying up to 5 times on '(timeout)'."""
    for attempt in range(1,6):  # Retry loop: max 5 attempts
        response = send_tello(command) # Send the command and get response
        print(f"Response: {response}") # Print what was received
        if response != '(timeout)':
            return response # Return immediately on valid response
        print(f"↻ Timeout #{attempt} for '{command}', retrying…") # Prints about retry
    return response # Return last response even if it's a timeout

def close_socket():
    """Cleanly close the socket."""
    global _sock
    if _sock:
        _sock.close() # Close the socket
        _sock = None # Reset the socket variable