import aioros2
from std_msgs.msg import Bool

a_topic = aioros2.topic("", Bool)

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
