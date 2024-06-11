import ctypes
import logging
import threading
import time
from typing import Optional, List, Tuple

from .laser_dac import LaserDAC

# Helios DAC uses 12 bits (unsigned) for x and y
X_BOUNDS = (0, 4095)
Y_BOUNDS = (0, 4095)

# Helios DAC uses 8 bits (unsigned) for r, g, b, i
MAX_COLOR = 255


# Define point structure for Helios
class HeliosPoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_uint16),
        ("y", ctypes.c_uint16),
        ("r", ctypes.c_uint8),
        ("g", ctypes.c_uint8),
        ("b", ctypes.c_uint8),
        ("i", ctypes.c_uint8),
    ]


class HeliosDAC(LaserDAC):
    """
    Helios DAC

    Example usage:

      dac = HeliosDAC()
      num_connected_dacs = dac.initialize()
      dac.connect(0)

      dac.set_color(1, 0, 0, 0.1)
      dac.add_point(0.1, 0.2)
      dac.play()
      ...
      dac.clear_points()
      dac.add_point(0.3, 0.4)
      ...
      dac.stop()
      dac.close()
    """

    points: List[Tuple[float, float]]
    color: Tuple[float, float, float, float]
    dac_idx: int
    playing: bool

    def __init__(self, lib_file: str, logger: Optional[logging.Logger] = None):
        """
        Args:
            lib_file (str): Path to native library file.
            logger (logging.Logger): Logger
        """
        self.points = []
        self._points_lock = threading.Lock()
        self.color = (1, 1, 1, 1)  # (r, g, b, i)
        self.dac_idx = -1
        self._lib = ctypes.cdll.LoadLibrary(lib_file)
        self.playing = False
        self._playback_thread = None
        self._check_connection = False
        self._check_connection_thread = None
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)
            self._logger.setLevel(logging.INFO)

    def initialize(self):
        """
        Initialize the native library and search for online DACs.
        """
        self._logger.info("Initializing Helios DAC")
        num_devices = self._lib.OpenDevices()
        self._logger.info(f"Found {num_devices} Helios DACs")
        return num_devices

    def connect(self, dac_idx: int):
        """
        Connect to the specified DAC.

        Args:
            dac_idx (int): Index of the DAC to connect to.
        """
        self.dac_idx = dac_idx

        def check_connection_thread():
            while self._check_connection:
                if self._get_status() < 0:
                    self._logger.warning(
                        f"DAC error {self._get_status()}. Attempting to reconnect."
                    )
                    self.stop()
                    self._lib.CloseDevices()
                    self.initialize()
                time.sleep(1)

        if self._check_connection_thread is None:
            self._check_connection = True
            self._check_connection_thread = threading.Thread(
                target=check_connection_thread, daemon=True
            )
            self._check_connection_thread.start()

    @property
    def is_connected(self) -> bool:
        """
        Returns:
            bool: Whether the DAC is connected.
        """
        return self.dac_idx >= 0 and self._get_status() >= 0

    def set_color(self, r: float, g: float, b: float, i: float):
        """
        Set the color of the laser.

        Args:
            r (float): Red channel, with value normalized to [0, 1]
            g (float): Green channel, with value normalized to [0, 1]
            b (float): Blue channel, with value normalized to [0, 1]
            i (float): Intensity, with value normalized to [0, 1]
        """
        self.color = (r, g, b, i)

    def add_point(self, x: float, y: float):
        """
        Add a point to be rendered by the DAC. (0, 0) corresponds to bottom left.
        The point will be ignored if it lies outside the bounds.

        Args:
            x (float): x coordinate normalized to [0, 1]
            y (float): y coordinate normalized to [0, 1]
        """
        if 0.0 <= x and x <= 1.0 and 0.0 <= y and y <= 1.0:
            with self._points_lock:
                self.points.append((x, y))

    def remove_point(self):
        """
        Remove the last added point.
        """
        with self._points_lock:
            if self.points:
                self.points.pop()

    def clear_points(self):
        """
        Remove all points.
        """
        with self._points_lock:
            self.points.clear()

    def _denormalize_point(self, x: float, y: float) -> Tuple[int, int]:
        x_denorm = round((X_BOUNDS[1] - X_BOUNDS[0]) * x + X_BOUNDS[0])
        y_denorm = round((Y_BOUNDS[1] - Y_BOUNDS[0]) * y + Y_BOUNDS[0])
        return (x_denorm, y_denorm)

    def _get_frame(self, fps: int, pps: int, transition_duration_ms: float):
        """
        Return an array of HeliosPoints representing the next frame that should be rendered.

        Args:
            fps (int): Target frames per second.
            pps (int): Target points per second. This should not exceed the capability of the DAC and laser projector.
            transition_duration_ms (float): Duration in ms to turn the laser off between subsequent points in the same
                frame. If we are rendering more than one point, we need to provide enough time between subsequent points,
                or else there may be visible streaks between the points as the galvos take time to move to the new position.
        """

        # We'll use "laxel", or laser "pixel", to refer to each point that the laser projector renders, which
        # disambiguates it from "point", which refers to the (x, y) coordinates we want to have rendered

        with self._points_lock:
            # Calculate how many laxels of transition we need to add per point
            laxels_per_transition = round(transition_duration_ms / (1000 / pps))

            # Calculate how many laxels we render each point
            ppf = pps / fps
            num_points = len(self.points)
            laxels_per_point = round(ppf if num_points == 0 else ppf / num_points)
            laxels_per_frame = (
                laxels_per_point if num_points == 0 else laxels_per_point * num_points
            )

            # Prepare frame
            FrameType = HeliosPoint * (laxels_per_frame)
            frame = FrameType()

            if num_points == 0:
                # Even if there are no points to render, we still to send over laxels so that we don't underflow the DAC buffer
                for frameLaxelIdx in range(laxels_per_frame):
                    frame[frameLaxelIdx] = HeliosPoint(0, 0, 0, 0, 0, 0)
            else:
                for pointIdx, point in enumerate(self.points):
                    for laxelIdx in range(laxels_per_point):
                        # Pad BEFORE the "on" laxel so that the galvo settles first, and only if there is more than one point
                        isTransition = (
                            num_points > 1 and laxelIdx < laxels_per_transition
                        )
                        frameLaxelIdx = pointIdx * laxels_per_point + laxelIdx
                        x, y = self._denormalize_point(point[0], point[1])
                        frame[frameLaxelIdx] = HeliosPoint(
                            x,
                            y,
                            0 if isTransition else int(self.color[0] * MAX_COLOR),
                            0 if isTransition else int(self.color[1] * MAX_COLOR),
                            0 if isTransition else int(self.color[2] * MAX_COLOR),
                            0 if isTransition else int(self.color[3] * MAX_COLOR),
                        )
            return frame

    def play(
        self, fps: int = 30, pps: int = 30000, transition_duration_ms: float = 0.5
    ):
        """
        Start playback of points.
        Helios max rate: 65535 pps
        Helios max points per frame (pps/fps): 4096

        Args:
            fps (int): Target frames per second.
            pps (int): Target points per second. This should not exceed the capability of the DAC and laser projector.
            transition_duration_ms (float): Duration in ms to turn the laser off between subsequent points in the same
                frame. If we are rendering more than one point, we need to provide enough time between subsequent points,
                or else there may be visible streaks between the points as the galvos take time to move to the new position.
        """
        fps = max(0, fps)
        pps = min(max(0, pps), 65535)

        def playback_thread():
            while self.playing:
                frame = self._get_frame(fps, pps, transition_duration_ms)
                statusAttempts = 0
                # Make 512 attempts for DAC status to be ready. After that, just give up and try to write the frame anyway
                while statusAttempts < 512 and self._lib.GetStatus(self.dac_idx) != 1:
                    statusAttempts += 1

                self._lib.WriteFrame(
                    self.dac_idx,
                    len(frame) * fps,
                    0,
                    ctypes.pointer(frame),
                    len(frame),
                )
            self._lib.Stop(self.dac_idx)

        if not self.playing:
            self.playing = True
            self._playback_thread = threading.Thread(
                target=playback_thread, daemon=True
            )
            self._playback_thread.start()

    def stop(self):
        """
        Stop playback of points.
        """
        if self.playing:
            self.playing = False
            if self._playback_thread:
                self._playback_thread.join()
                self._playback_thread = None

    def close(self):
        """
        Close connection to laser DAC.
        """
        self.stop()
        if self._check_connection:
            self._check_connection = False
            if self._check_connection_thread:
                self._check_connection_thread.join()
                self._check_connection_thread = None
        self._lib.CloseDevices()
        self.dac_idx = -1

    def _get_status(self):
        # 1 means ready to receive frame
        # 0 means not ready to receive frame
        # Any negative status means error
        return self._lib.GetStatus(self.dac_idx)
