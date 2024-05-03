import asyncio
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

import numpy as np
from scipy.optimize import least_squares, minimize

from camera_control.camera_control_node import CameraControlNode
from common_interfaces.msg import Vector2
from laser_control.laser_control_node import LaserControlNode


class Calibration:
    is_calibrated: bool
    camera_to_laser_transform: np.ndarray
    camera_frame_size: Tuple[int, int]

    def __init__(
        self,
        laser_node: LaserControlNode,
        camera_node: CameraControlNode,
        laser_color: Tuple[float, float, float],
        logger: Optional[logging.Logger] = None,
    ):
        self._laser_node = laser_node
        self._camera_node = camera_node
        self._laser_color = laser_color
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger(__name__)
            self._logger.setLevel(logging.INFO)

        self._calibration_laser_coords = []
        self._calibration_camera_points = []
        self.is_calibrated = False
        self.camera_to_laser_transform = np.zeros((4, 3))
        self.camera_frame_size = (0, 0)

    def reset(self):
        self.camera_to_laser_transform = np.zeros((4, 3))
        self._calibration_laser_coords = []
        self._calibration_camera_points = []
        self.is_calibrated = False

    async def calibrate(self) -> bool:
        """
        Use image correspondences to compute the transformation matrix from camera to laser.
        Note that calling this resets the point correspondences.

        1. Shoot the laser at predetermined points
        2. For each laser point, capture an image from the camera
        3. Identify the corresponding point in the camera frame
        4. Compute the transformation matrix from camera to laser

        Returns:
            bool: Whether calibration was successful or not.
        """
        self.reset()

        # TODO: Depth values are noisy when the laser is on. Figure out how to reduce noise, or
        # use a depth frame obtained when the laser is off

        # Get camera color frame size
        result = await self._camera_node.get_frame()
        self.camera_frame_size = (result.color_frame.width, result.color_frame.height)

        # Get calibration points
        grid_size = (5, 5)
        x_step = 1.0 / (grid_size[0] - 1)
        y_step = 1.0 / (grid_size[1] - 1)
        pending_calibration_laser_coords = []
        for i in range(grid_size[0]):
            for j in range(grid_size[1]):
                x = i * x_step
                y = j * y_step
                pending_calibration_laser_coords.append((x, y))

        # Get image correspondences
        self._logger.info("Get image correspondences")
        await self.add_calibration_points(pending_calibration_laser_coords)

        self._logger.info(
            f"{len(self._calibration_laser_coords)} out of {len(pending_calibration_laser_coords)} point correspondences found."
        )

        if len(self._calibration_laser_coords) < 3:
            self._logger.warning(
                "Calibration failed: insufficient point correspondences found."
            )
            return False

        # Use linear least squares for an initial estimate, then refine using nonlinear least squares
        self._update_transform_linear_least_squares()
        await self._update_transform_nonlinear_least_squares()

        self.is_calibrated = True
        return True

    async def add_calibration_points(
        self, laser_coords: List[Tuple[float, float]], update_transform: bool = False
    ):
        """
        Find and add additional point correspondences by shooting the laser at each laser_coords
        and then optionally recalculate the transform.

        Args:
            laser_coords (List[Tuple[float, float]]): laser coordinates to find point correspondences with
            update_transform (bool): Whether to recalculate the camera-space position to laser coord transform
        """

        # TODO: set exposure on camera node automatically when detecting laser
        await self._camera_node.set_exposure(exposure_us=1.0)
        self._logger.info("laser node set 0 color")
        await self._laser_node.set_color(r=0.0, g=0.0, b=0.0, i=0.0)
        self._logger.info("laser node play")
        await self._laser_node.play()
        for laser_coord in laser_coords:
            await self._laser_node.set_points(
                points=[Vector2(x=laser_coord[0], y=laser_coord[1])]
            )
            await self._laser_node.set_color(
                r=self._laser_color[0],
                g=self._laser_color[1],
                b=self._laser_color[2],
                i=0.0,
            )
            self._logger.info("laser set color")
            # Wait for galvo to settle and for camera frame capture
            await asyncio.sleep(0.1)
            camera_point = await self._find_point_correspondence(laser_coord)
            if camera_point is not None:
                await self.add_point_correspondence(laser_coord, camera_point)
            # We use set_color instead of stop_laser as it is faster to temporarily turn off the laser
            await self._laser_node.set_color(r=0.0, g=0.0, b=0.0, i=0.0)

        await self._laser_node.stop()
        await self._camera_node.auto_exposure()

        if update_transform:
            await self._update_transform_nonlinear_least_squares()

    def camera_point_to_laser_coord(
        self, position: Tuple[float, float, float]
    ) -> Tuple[float, float]:
        """
        Transform a 3D position in camera-space to a laser coord.

        Args:
            position (Tuple[float, float, float]): A 3D position (x, y, z) in camera-space.
        """
        homogeneous_camera_point = np.hstack((position, 1))
        transformed_point = homogeneous_camera_point @ self.camera_to_laser_transform
        transformed_point = transformed_point / transformed_point[2]
        return (transformed_point[0], transformed_point[1])

    async def _find_point_correspondence(
        self, laser_coord: Tuple[float, float], num_attempts: int = 3
    ) -> Optional[Tuple[float, float, float]]:
        """
        For the given laser coord, find the corresponding 3D point in camera-space.

        Args:
            laser_coord (Tuple[float, float]): Laser coordinate (x, y) to find point correspondence for.
            num_attempts (int): Number of tries to detect the laser and find the point correspondence.
        """
        attempt = 0
        while attempt < num_attempts:
            self._logger.info(
                f"Attempt {attempt} to detect laser and find point correspondence."
            )
            attempt += 1
            result = await self._camera_node.get_laser_detection()
            detection_result = result.result
            instances = detection_result.instances
            if instances:
                # TODO: handle case where multiple lasers detected
                instance = instances[0]
                self._logger.info(
                    f"Found point correspondence: laser_coord = {laser_coord}, pixel = {instance.point}, position = {instance.position}."
                )
                return (instance.position.x, instance.position.y, instance.position.z)
            await asyncio.sleep(0.2)
        self._logger.info(
            f"Failed to find point. {len(self._calibration_laser_coords)} total correspondences."
        )
        return None

    async def add_point_correspondence(
        self,
        laser_coord: Tuple[float, float],
        camera_point: Tuple[float, float, float],
        update_transform: bool = False,
    ):
        """
        Add the point correspondence between laser coord and camera-space position and optionally
        update the transform.

        Args:
            laser_coord (Tuple[float, float]): Laser coordinate (x, y) of the point correspondence.
            camera_point (Tuple[float, float, float]): Camera-space position (x, y, z) of the point correspondence.
            update_transform (bool): Whether to update the transform matrix or not.
        """
        self._calibration_laser_coords.append(laser_coord)
        self._calibration_camera_points.append(camera_point)
        self._logger.info(
            f"Added point correspondence. {len(self._calibration_laser_coords)} total correspondences."
        )

        if update_transform:
            await self._update_transform_nonlinear_least_squares()

    async def _update_transform_nonlinear_least_squares(self):
        def residuals(parameters, camera_points, laser_coords):
            homogeneous_camera_points = np.hstack(
                (camera_points, np.ones((camera_points.shape[0], 1)))
            )
            transform = parameters.reshape((4, 3))
            transformed_points = np.dot(homogeneous_camera_points, transform)
            homogeneous_transformed_points = (
                transformed_points[:, :2] / transformed_points[:, 2][:, np.newaxis]
            )
            return (homogeneous_transformed_points[:, :2] - laser_coords).flatten()

        camera_points = np.array(self._calibration_camera_points)
        laser_coords = np.array(self._calibration_laser_coords)

        with ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                functools.partial(
                    least_squares,
                    residuals,
                    self.camera_to_laser_transform.flatten(),
                    args=(camera_points, laser_coords),
                    method="trf",
                ),
            )

        self.camera_to_laser_transform = result.x.reshape((4, 3))

        self._logger.info(
            "Updated camera to laser transform using nonlinear least squares"
        )
        self._get_reprojection_error(
            camera_points, laser_coords, self.camera_to_laser_transform
        )

    async def _update_transform_bundle_adjustment(self):
        def cost_function(parameters, camera_points, laser_coords):
            homogeneous_camera_points = np.hstack(
                (camera_points, np.ones((camera_points.shape[0], 1)))
            )
            transform = parameters.reshape((4, 3))
            transformed_points = np.dot(homogeneous_camera_points, transform)
            homogeneous_transformed_points = (
                transformed_points[:, :2] / transformed_points[:, 2][:, np.newaxis]
            )
            errors = np.sum(
                (homogeneous_transformed_points[:, :2] - laser_coords) ** 2, axis=1
            )
            return np.mean(errors)

        camera_points = np.array(self._calibration_camera_points)
        laser_coords = np.array(self._calibration_laser_coords)

        with ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                functools.partial(
                    minimize,
                    cost_function,
                    self.camera_to_laser_transform.flatten(),
                    args=(camera_points, laser_coords),
                    method="L-BFGS-B",
                ),
            )

        self.camera_to_laser_transform = result.x.reshape((4, 3))

        self._logger.info("Updated camera to laser transform using bundle adjustment")
        self._get_reprojection_error(
            camera_points, laser_coords, self.camera_to_laser_transform
        )

    def _update_transform_linear_least_squares(self):
        camera_points = np.array(self._calibration_camera_points)
        laser_coords = np.array(self._calibration_laser_coords)
        homogeneous_laser_coords = np.hstack(
            (laser_coords, np.ones((laser_coords.shape[0], 1)))
        )
        homogeneous_camera_points = np.hstack(
            (camera_points, np.ones((camera_points.shape[0], 1)))
        )
        self.camera_to_laser_transform = np.linalg.lstsq(
            homogeneous_camera_points,
            homogeneous_laser_coords,
            rcond=None,
        )[0]

        self._logger.info(
            "Updated camera to laser transform using linear least squares"
        )
        self._get_reprojection_error(
            camera_points, laser_coords, self.camera_to_laser_transform
        )

    def _get_reprojection_error(
        self,
        camera_points: np.ndarray,
        laser_coords: np.ndarray,
        camera_to_laser_transform: np.ndarray,
    ) -> float:
        self._logger.info(f"Laser coords:\n{laser_coords}")
        homogeneous_camera_points = np.hstack(
            (camera_points, np.ones((camera_points.shape[0], 1)))
        )
        transformed_points = np.dot(
            homogeneous_camera_points, camera_to_laser_transform
        )
        homogeneous_transformed_points = (
            transformed_points[:, :2] / transformed_points[:, 2][:, np.newaxis]
        )
        self._logger.info(
            f"Laser coords calculated using transform:\n{homogeneous_transformed_points[:, :2]}"
        )
        reprojection_error = np.mean(
            np.sqrt(
                np.sum(
                    (homogeneous_transformed_points[:, :2] - laser_coords) ** 2,
                    axis=1,
                )
            )
        )
        self._logger.info(f"Mean reprojection error: {reprojection_error}")
        return reprojection_error
