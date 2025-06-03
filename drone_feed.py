#!/usr/bin/env python3
"""
Tello Drone Video Feed (flat functions)
Displays the live camera feed in a fixed-size, borderless PIP snapped to the bottom-right.
"""

import time
import cv2
from ctypes import windll

# Configuration
TELLO_PORT = 11111       # UDP port where Tello streams video
DELAY = 5                # seconds to wait when no frame is received
PIP_W, PIP_H = 320, 240  # picture-in-picture window size (width, height)
MARGIN = 10              # pixels from screen edges

# Win32 window style constants
GWL_STYLE      = -16           # Index for getting/setting the window's style with GetWindowLong
WS_POPUP       = 0x80000000    # Style for a popup window (no border or title bar)
WS_CAPTION     = 0x00C00000    # Style that gives the window a title bar (includes border)
WS_THICKFRAME  = 0x00040000    # Enables resizing by dragging window borders
WS_MINIMIZEBOX = 0x00020000    # Adds a minimize button to the title bar
WS_MAXIMIZEBOX = 0x00010000    # Adds a maximize button to the title bar
WS_SYSMENU     = 0x00080000    # Enables the system menu (with options like Close, Move, etc.)

# Combines multiple window styles to create a standard, resizable window with system controls
OVERLAPPED     = (WS_CAPTION | WS_THICKFRAME |
                  WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)

SWP_NOSIZE     = 0x0001        # When repositioning a window, don't change its size
SWP_NOACTIVATE = 0x0010        # Don’t activate the window (i.e., don’t give it keyboard focus)
SWP_SHOWWINDOW = 0x0040        # Makes sure the window is shown (if hidden)

HWND_TOPMOST   = -1            # Special handle that places the window above all non-topmost windows (keeps it always on top)

def open_capture(port):
    """
    Open the UDP video stream from the Tello drone via OpenCV.
    """
    cap = cv2.VideoCapture(f'udp://0.0.0.0:{port}')  # connect to Tello feed
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video stream on port {port}")
    print(f"Receiving Tello video stream on port {port}")  # log success
    return cap

def setup_window(name):
    """
    Creates and sizes a resizable OpenCV window for the feed.
    """
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)  # make window resizable
    cv2.resizeWindow(name, PIP_W, PIP_H)      # set window to PIP size
    cv2.waitKey(1)                            # pump events once
    time.sleep(0.05)                          # small delay for init

def position_window(name):
    """
    Uses Win32 APIs to make the window borderless, always-on-top and snap the window to the bottom-right corner.
    """
    sw = windll.user32.GetSystemMetrics(0)  # screen width
    sh = windll.user32.GetSystemMetrics(1)  # screen height
    x = sw - PIP_W - MARGIN                 # compute right-edge x
    y = sh - PIP_H - MARGIN                 # compute bottom-edge y

    hwnd = windll.user32.FindWindowW(None, name)
    if hwnd:
        style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)  # current style
        new_style = (style & ~OVERLAPPED) | WS_POPUP           # popup style
        windll.user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)  # apply style
        windll.user32.SetWindowPos(
            hwnd, HWND_TOPMOST, x, y, 0, 0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW       # keep size, pos
        )
        cv2.moveWindow(name, x, y)  # adjust OpenCV’s idea of window position
    else:
        print(f"Could not find window '{name}' to style/position")  # warn

def main_loop(cap, window_name):
    """
    Grabs frames from the VideoCapture and shows them.
    """
    try:
        while True:
            ret, frame = cap.read()  # attempt to read a frame
            if not ret:
                time.sleep(DELAY)    # no frame? back off briefly
                continue

            cv2.imshow(window_name, frame)  # show frame
            cv2.waitKey(1)                  # pump the window loop
            time.sleep(0.001)               # tiny pause to reduce CPU load
    finally:
        cap.release()                   # close the UDP stream
        cv2.destroyWindow(window_name)  # remove the PIP window
        print("Video stream stopped")   # log teardown

'''Initial setup: open stream, warm up, create and position window.'''
def initialize():
    name = "Tello Camera Feed"
    cap = open_capture(TELLO_PORT)  # start receiving
    time.sleep(2)                   # warm up the stream
    setup_window(name)              # create & size window
    position_window(name)           # borderless + always-on-top
    return cap, name

'''Entry point to wire everything together and start the feed.'''
def run():
    cap, name = initialize() # Prepare drone feed and window display
    main_loop(cap, name)     # show drone frames

if __name__ == "__main__":
    run()
