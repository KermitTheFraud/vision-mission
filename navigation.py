# navigation.py

def make_scale_converter(pixel_ref, real_cm_ref):
    """
    Create a converter that maps pixel coordinates to centimeters based on a calibration reference.

    Args:
        pixel_ref: Distance in pixels between two known calibration points.
        real_cm_ref: Actual distance in centimeters between those same calibration points.

    Returns:
        coord_to_cm: A function that takes an (x, y) pixel coordinate and returns its (x, y) position in centimeters.
    """
    cm_per_pixel = real_cm_ref / pixel_ref

    def coord_to_cm(x_px, y_px):
        """
        Convert a pixel coordinate to centimeters relative to the origin.

        Args:
            x_px: X-coordinate in pixels.
            y_px: Y-coordinate in pixels.

        Returns:
            (x_cm, y_cm) in centimeters.
        """
        return (x_px * cm_per_pixel, y_px * cm_per_pixel)

    return coord_to_cm


def calculate_moves(start, end):
    """
    Compute the relative movement vector between two positions.

    Args:
        start: Starting coordinates (x, y) in centimeters.
        end: Destination coordinates (x, y) in centimeters.

    Returns:
        forward: Positive means forward, negative means backward.
        sideways: Positive means right, negative means left.
    """
    x1, y1 = start
    x2, y2 = end

    forward = y2 - y1
    sideways = x2 - x1

    return forward, sideways


def calculate_udp(forward, sideways):
    """
    Convert movement distances into Tello UDP command strings.

    Args:
        forward: Distance in centimeters (positive for forward, negative for backward).
        sideways: Distance in centimeters (positive for right, negative for left).

    Returns:
        forward_cmd: 'forward <value>' or 'back <value>'.
        sideways_cmd: 'right <value>' or 'left <value>'.
    """
    if forward >= 0:
        forward_cmd = f'forward {forward}'
    else:
        forward_cmd = f'back {abs(forward)}'

    if sideways >= 0:
        sideways_cmd = f'right {sideways}'
    else:
        sideways_cmd = f'left {abs(sideways)}'

    return forward_cmd, sideways_cmd


# Pre-calibrated converter using default reference values (1920 px = 300 cm)
coord_to_cm = make_scale_converter(pixel_ref=1920, real_cm_ref=300)


def calculate_from_pixels(start_px, end_px):
    """
    High-level helper: convert pixel coordinates to UDP command strings with a 90° right rotation.

    This function applies the default calibration, computes the move vector,
    rotates it so that original 'right' becomes forward, rounds to the nearest integer,
    and formats Tello-compatible commands.

    Args:
        start_px: Start position in pixels (x, y).
        end_px: End position in pixels (x, y).

    Returns:
        (forward_cmd, sideways_cmd)
    """
    start_cm = coord_to_cm(*start_px)
    end_cm = coord_to_cm(*end_px)

    forward, sideways = calculate_moves(start_cm, end_cm)

    new_forward = sideways
    new_sideways = -forward

    return calculate_udp(round(new_forward), round(new_sideways))
