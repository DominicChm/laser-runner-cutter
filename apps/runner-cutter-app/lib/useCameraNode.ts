import type { NodeInfo } from "@/lib/NodeInfo";
import useROS from "@/lib/ros/useROS";
import { useCallback, useEffect, useMemo, useState } from "react";

export type State = {
  deviceState: DeviceState;
  laserDetectionEnabled: boolean;
  runnerDetectionEnabled: boolean;
  recordingVideo: boolean;
  intervalCaptureActive: boolean;
  exposureUs: number;
  exposureUsRange: [number, number];
  gainDb: number;
  gainDbRange: [number, number];
  saveDirectory: string;
};
export enum DeviceState {
  Disconnected,
  Connecting,
  Streaming,
}

function convertStateMessage(message: any): State {
  return {
    deviceState: message.device_state.data as DeviceState,
    laserDetectionEnabled: message.laser_detection_enabled,
    runnerDetectionEnabled: message.runner_detection_enabled,
    recordingVideo: message.recording_video,
    intervalCaptureActive: message.interval_capture_active,
    exposureUs: message.exposure_us,
    exposureUsRange: [message.exposure_us_range.x, message.exposure_us_range.y],
    gainDb: message.gain_db,
    gainDbRange: [message.gain_db_range.x, message.gain_db_range.y],
    saveDirectory: message.save_directory,
  };
}

function convertToLocalReadableTime(secondsSinceEpoch: number) {
  const date = new Date(secondsSinceEpoch * 1000);
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const seconds = date.getSeconds().toString().padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

export default function useCameraNode(nodeName: string) {
  const { nodeInfo: rosbridgeNodeInfo, ros } = useROS();
  const [nodeConnected, setNodeConnected] = useState<boolean>(false);
  const [nodeState, setNodeState] = useState<State>({
    deviceState: DeviceState.Disconnected,
    laserDetectionEnabled: false,
    runnerDetectionEnabled: false,
    recordingVideo: false,
    intervalCaptureActive: false,
    exposureUs: 0.0,
    exposureUsRange: [0.0, 0.0],
    gainDb: 0.0,
    gainDbRange: [0.0, 0.0],
    saveDirectory: "",
  });
  const [logMessages, setLogMessages] = useState<string[]>([]);

  const nodeInfo: NodeInfo = useMemo(() => {
    return {
      name: nodeName,
      connected: rosbridgeNodeInfo.connected && nodeConnected,
      state: nodeState,
    };
  }, [nodeName, rosbridgeNodeInfo, nodeConnected, nodeState]);

  const addLogMessage = useCallback(
    (logMessage: string) => {
      setLogMessages((prevLogMessages) => {
        const newLogMessages = [...prevLogMessages, logMessage];
        return newLogMessages.slice(-10);
      });
    },
    [setLogMessages]
  );

  // Subscriptions
  useEffect(() => {
    const onNodeConnectedSub = ros.onNodeConnected(
      (connectedNodeName, connected) => {
        if (connectedNodeName === nodeName) {
          setNodeConnected(connected);
        }
      }
    );

    const stateSub = ros.subscribe(
      `${nodeName}/state`,
      "camera_control_interfaces/State",
      (message) => {
        setNodeState(convertStateMessage(message));
      }
    );

    const logSub = ros.subscribe(
      `${nodeName}/log`,
      "rcl_interfaces/Log",
      (message) => {
        const timestamp_sec = parseInt(message["stamp"]["sec"]);
        const msg = `[${convertToLocalReadableTime(timestamp_sec)}] ${
          message["msg"]
        }`;
        addLogMessage(msg);
      }
    );

    return () => {
      onNodeConnectedSub.unsubscribe();
      stateSub.unsubscribe();
      logSub.unsubscribe();
    };
  }, [ros, nodeName, setNodeConnected, setNodeState, addLogMessage]);

  const startDevice = useCallback(() => {
    // Optimistically set device state to "connecting"
    setNodeState((state) => {
      return {
        ...state,
        deviceState: DeviceState.Connecting,
      };
    });
    ros.callService(`${nodeName}/start_device`, "std_srvs/Trigger", {});
  }, [ros, nodeName, setNodeState]);

  const closeDevice = useCallback(() => {
    ros.callService(`${nodeName}/close_device`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  const setExposure = useCallback(
    (exposureUs: number) => {
      ros.callService(
        `${nodeName}/set_exposure`,
        "camera_control_interfaces/SetExposure",
        { exposure_us: exposureUs }
      );
    },
    [ros, nodeName]
  );

  const autoExposure = useCallback(() => {
    ros.callService(`${nodeName}/auto_exposure`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  const setGain = useCallback(
    (gainDb: number) => {
      ros.callService(
        `${nodeName}/set_gain`,
        "camera_control_interfaces/SetGain",
        { gain_db: gainDb }
      );
    },
    [ros, nodeName]
  );

  const autoGain = useCallback(() => {
    ros.callService(`${nodeName}/auto_gain`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  const setSaveDirectory = useCallback(
    (saveDir: string) => {
      ros.callService(
        `${nodeName}/set_save_directory`,
        "camera_control_interfaces/SetSaveDirectory",
        { save_directory: saveDir }
      );
    },
    [ros, nodeName]
  );

  const startLaserDetection = useCallback(() => {
    ros.callService(
      `${nodeName}/start_laser_detection`,
      "std_srvs/Trigger",
      {}
    );
  }, [ros, nodeName]);

  const stopLaserDetection = useCallback(() => {
    ros.callService(`${nodeName}/stop_laser_detection`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  const startRunnerDetection = useCallback(() => {
    ros.callService(
      `${nodeName}/start_runner_detection`,
      "std_srvs/Trigger",
      {}
    );
  }, [ros, nodeName]);

  const stopRunnerDetection = useCallback(() => {
    ros.callService(
      `${nodeName}/stop_runner_detection`,
      "std_srvs/Trigger",
      {}
    );
  }, [ros, nodeName]);

  const startRecordingVideo = useCallback(() => {
    ros.callService(
      `${nodeName}/start_recording_video`,
      "std_srvs/Trigger",
      {}
    );
  }, [ros, nodeName]);

  const stopRecordingVideo = useCallback(() => {
    ros.callService(`${nodeName}/stop_recording_video`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  const startIntervalCapture = useCallback(
    (intervalSecs: number) => {
      ros.callService(
        `${nodeName}/start_interval_capture`,
        "camera_control_interfaces/StartIntervalCapture",
        { interval_secs: intervalSecs }
      );
    },
    [ros, nodeName]
  );

  const stopIntervalCapture = useCallback(() => {
    ros.callService(
      `${nodeName}/stop_interval_capture`,
      "std_srvs/Trigger",
      {}
    );
  }, [ros, nodeName]);

  const saveImage = useCallback(() => {
    ros.callService(`${nodeName}/save_image`, "std_srvs/Trigger", {});
  }, [ros, nodeName]);

  return {
    nodeInfo,
    nodeState,
    logMessages,
    startDevice,
    closeDevice,
    setExposure,
    autoExposure,
    setGain,
    autoGain,
    setSaveDirectory,
    startLaserDetection,
    stopLaserDetection,
    startRunnerDetection,
    stopRunnerDetection,
    startRecordingVideo,
    stopRecordingVideo,
    startIntervalCapture,
    stopIntervalCapture,
    saveImage,
  };
}
