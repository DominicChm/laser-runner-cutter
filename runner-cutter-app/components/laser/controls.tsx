"use client";

import { useEffect, useState } from "react";
import useROS from "@/lib/ros/useROS";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ColorPicker from "@/components/laser/color-picker";

const LASER_STATES = ["disconnected", "stopped", "playing"];

function hexToRgb(hexColor: string) {
  hexColor = hexColor.replace("#", "");
  const r = parseInt(hexColor.substring(0, 2), 16) / 255.0;
  const g = parseInt(hexColor.substring(2, 4), 16) / 255.0;
  const b = parseInt(hexColor.substring(4, 6), 16) / 255.0;
  return { r, g, b };
}

export default function Controls() {
  const { ros, callService, subscribe } = useROS();
  const [rosConnected, setRosConnected] = useState<boolean>(false);
  // TODO: add ability to select laser node name
  const [nodeName, setNodeName] = useState<string>("/laser0");
  const [laserState, setLaserState] = useState<number>(0);
  const [color, setColor] = useState<string>("#ff0000");
  const [x, setX] = useState<number>(0);
  const [y, setY] = useState<number>(0);

  useEffect(() => {
    // TODO: add listener for rosbridge connection state
    setRosConnected(ros.isConnected);
  }, []);

  // Initial node state
  useEffect(() => {
    const getState = async () => {
      const result = await callService(
        `${nodeName}/get_state`,
        "laser_control_interfaces/GetState",
        {}
      );
      setLaserState(result.state.data);
    };
    getState();
  }, [nodeName]);

  // Subscriptions
  useEffect(() => {
    const stateSub = subscribe(
      `${nodeName}/state`,
      "laser_control_interfaces/State",
      (message) => {
        setLaserState(message.data);
      }
    );
    return () => {
      stateSub.unsubscribe();
    };
  }, [nodeName]);

  const onAddPointClick = () => {
    callService(`${nodeName}/add_point`, "laser_control_interfaces/AddPoint", {
      point: {
        x: x,
        y: y,
      },
    });
  };

  const onClearPointsClick = () => {
    callService(`${nodeName}/clear_points`, "std_srvs/Empty", {});
  };

  const onPlayClick = () => {
    callService(`${nodeName}/play`, "std_srvs/Empty", {});
  };

  const onStopClick = () => {
    callService(`${nodeName}/stop`, "std_srvs/Empty", {});
  };

  const onColorChange = (color: string) => {
    setColor(color);
    const rgb = hexToRgb(color);
    callService(`${nodeName}/set_color`, "laser_control_interfaces/SetColor", {
      r: rgb.r,
      g: rgb.g,
      b: rgb.b,
      i: 0.0,
    });
  };

  let laserButton = null;
  if (laserState === 1) {
    laserButton = (
      <Button disabled={!rosConnected} onClick={onPlayClick}>
        Start Laser
      </Button>
    );
  } else if (laserState === 2) {
    laserButton = (
      <Button disabled={!rosConnected} onClick={onStopClick}>
        Stop Laser
      </Button>
    );
  }

  return (
    <div className="flex flex-col gap-4 items-center">
      <div className="flex flex-col items-center">
        <p className="text-center">{`Rosbridge: ${
          rosConnected ? "connected" : "disconnected"
        }`}</p>
        <p className="text-center">{`Laser (${nodeName}): ${LASER_STATES[laserState]}`}</p>
      </div>
      <div className="flex flex-row gap-4 items-center">
        <Input
          className="flex-none w-20"
          type="number"
          id="x"
          name="x"
          placeholder="x"
          step={0.1}
          value={x.toString()}
          onChange={(event) => {
            const value = Number(event.target.value);
            setX(isNaN(value) ? 0 : value);
          }}
        />
        <Input
          className="flex-none w-20"
          type="number"
          id="y"
          name="y"
          placeholder="y"
          step={0.1}
          value={y.toString()}
          onChange={(event) => {
            const value = Number(event.target.value);
            setY(isNaN(value) ? 0 : value);
          }}
        />
        <Button disabled={!rosConnected} onClick={onAddPointClick}>
          Add Point
        </Button>
        <Button disabled={!rosConnected} onClick={onClearPointsClick}>
          Clear Points
        </Button>
      </div>
      <div className="flex flex-row items-center gap-4">
        <ColorPicker color={color} onColorChange={onColorChange} />
      </div>
      <div className="flex flex-row items-center gap-4">{laserButton}</div>
    </div>
  );
}
