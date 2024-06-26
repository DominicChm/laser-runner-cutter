import { useContext, useEffect, useMemo, useState } from "react";
import ROSContext from "@/lib/ros/ROSContext";
import type { NodeInfo } from "@/lib/NodeInfo";

export default function useROS() {
  const ros = useContext(ROSContext);
  const [rosConnected, setRosConnected] = useState<boolean>(false);

  const nodeInfo: NodeInfo = useMemo(() => {
    return {
      name: "Rosbridge",
      connected: rosConnected,
    };
  }, [rosConnected]);

  useEffect(() => {
    ros.onStateChange(() => {
      setRosConnected(ros.isConnected());
    });
    setRosConnected(ros.isConnected());
  }, [ros, setRosConnected]);

  return { nodeInfo, ros };
}
