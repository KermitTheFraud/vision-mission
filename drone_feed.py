#!/usr/bin/env python3
"""
Tello Drone Video Feed (flat functions)
Displays the live camera feed in a fixed-size, borderless PIP snapped to the bottom-right.
"""

import time
import cv2
import numpy as np
from ctypes import windll

# Configuration
TELLO_PORT = 11111       # UDP port where Tello streams video
DELAY = 5                # seconds to wait when no frame is received
PIP_W, PIP_H = 320, 240  # picture-in-picture window size (width, height)
MARGIN = 10              # pixels from screen edges

# Win32 window style constants
GWL_STYLE      = -16
WS_POPUP       = 0x80000000
WS_CAPTION     = 0x00C00000
WS_THICKFRAME  = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU     = 0x00080000
OVERLAPPED     = (WS_CAPTION | WS_THICKFRAME |
                  WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
SWP_NOSIZE     = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST   = -1

'''Open the UDP video stream from the Tello drone.'''
def open_capture(port):
    """
    Opens the cv2.VideoCapture for the given UDP port.
    """
    cap = cv2.VideoCapture(f'udp://0.0.0.0:{port}')  # connect to Tello feed
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video stream on port {port}")
    print(f"Receiving Tello video stream on port {port}")  # log success
    return cap

'''Prepare the OpenCV window for the PIP display.'''
def setup_window(name):
    """
    Creates and sizes a resizable OpenCV window for the feed.
    """
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)            # make window resizable
    cv2.resizeWindow(name, PIP_W, PIP_H)                # set window to PIP size
    blank = np.zeros((PIP_H, PIP_W, 3), dtype=np.uint8) # blank frame buffer
    cv2.imshow(name, blank)                             # force window creation
    cv2.waitKey(1)                                      # pump events once
    time.sleep(0.05)                                    # small delay for init

'''Strip borders and snap the window to the bottom-right corner.'''
def position_window(name):
    """
    Uses Win32 APIs to make the window borderless and always-on-top.
    """
    sw = windll.user32.GetSystemMetrics(0)  # screen width
    sh = windll.user32.GetSystemMetrics(1)  # screen height
    x = sw - PIP_W - MARGIN                  # compute right-edge x
    y = sh - PIP_H - MARGIN                  # compute bottom-edge y

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
        print(f" Could not find window '{name}' to style/position")  # warn

'''Main loop: continuously read frames and display them.'''
def main_loop(cap, window_name):
    """
    Grabs frames from the VideoCapture and shows them until the user quits.
    """
    try:
        while True:
            ret, frame = cap.read()  # attempt to read a frame
            if not ret:
                time.sleep(DELAY)    # no frame? back off briefly
                continue

            cv2.imshow(window_name, frame)  # render to PIP
            cv2.waitKey(1)                  # pump the window loop
            time.sleep(0.001)                # tiny pause to reduce CPU load
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
    cap, name = initialize()
    main_loop(cap, name)

if __name__ == "__main__":
    run()
