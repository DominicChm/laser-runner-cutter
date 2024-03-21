import { useEffect, useState } from "react";
import useROS from "@/lib/ros/useROS";

export default function useControlNode(nodeName: string) {
  const { callService, subscribe } = useROS();
  const [nodeState, setNodeState] = useState({
    calibrated: false,
    state: "disconnected",
  });

  // Initial node state
  useEffect(() => {
    const getState = async () => {
      const result = await callService(
        `${nodeName}/get_state`,
        "runner_cutter_control_interfaces/GetState",
        {}
      );
      setNodeState(result.state);
    };
    getState();
  }, [nodeName]);

  // Subscriptions
  useEffect(() => {
    const stateSub = subscribe(
      `${nodeName}/state`,
      "runner_cutter_control_interfaces/State",
      (message) => {
        setNodeState(message);
      }
    );

    return () => {
      stateSub.unsubscribe();
    };
  }, [nodeName]);

  const calibrate = () => {
    callService(`${nodeName}/calibrate`, "std_srvs/Trigger", {});
  };

  const addCalibrationPoint = (x: number, y: number) => {
    callService(
      `${nodeName}/add_calibration_points`,
      "runner_cutter_control_interfaces/AddCalibrationPoints",
      { camera_pixels: [{ x, y }] }
    );
  };

  const startRunnerCutter = () => {
    callService(`${nodeName}/start_runner_cutter`, "std_srvs/Trigger", {});
  };

  const stop = () => {
    callService(`${nodeName}/stop`, "std_srvs/Trigger", {});
  };

  return {
    calibrated: nodeState.calibrated,
    controlState: nodeState.state,
    calibrate,
    addCalibrationPoint,
    startRunnerCutter,
    stop,
  };
}
