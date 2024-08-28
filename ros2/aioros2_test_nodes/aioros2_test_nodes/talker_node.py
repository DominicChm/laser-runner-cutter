import aioros2.patch_import
from std_srvs.srv import Trigger
from dataclasses import dataclass
import aioros2

from . import other_node as onode, talker_node as tnode
@dataclass
class TalkerParams:
    amiga_host: str = "10.95.76.1"
    canbus_service_port: int = 6001


# Executable to call to launch this node (defined in `setup.py`)
# amiga_params = aioros2.params(TalkerParams)
# amiga_available = aioros2.topic("~/available", Bool, aioros2.QOS_LATCHED)

@aioros2.start
async def start():
    print("Running...!")
    pass
    # other_t1.set_twist()

# @subscribe(other_node.a_topic)

@aioros2.service("~/start", Trigger)
async def start_lel() -> bool:
    print("SERVICE CALLED!")
    return {"success": True}

@aioros2.timer(1, True)
async def t():
    # print("TIMER")
    # await asyncio.sleep(5)
    pass

# Boilerplate below here.
def main():
    aioros2.run()

if __name__ == "__main__":
    main()
