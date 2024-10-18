from std_srvs.srv import Trigger
from std_msgs.msg import String
from dataclasses import dataclass
import aioros2

#  colcon build --packages-select aioros2_test_nodes --symlink-install && ros2 run aioros2_test_nodes talk --ros-args -p "onode.name:=onode" -p "onode.namespace:=/"

@dataclass
class TalkerParams:
    amiga_host: str = "10.95.76.1"
    canbus_service_port: int = 6001
params = aioros2.params(TalkerParams)

topic_test = aioros2.topic("~/test", String)


@aioros2.start
async def start():
    print(params.amiga_host)
    print("Running...!")
    pass

@aioros2.timer(1)
async def talk():
    topic_test.pub(data="test")
    
# Boilerplate below here.
def main():
    aioros2.run()

if __name__ == "__main__":
    main()
