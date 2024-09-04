import aioros2
from std_msgs.msg import Bool

a_topic = aioros2.topic("lel", Bool)

@aioros2.timer(1, True)
async def t():
    a_topic.pub(data=True)

# Boilerplate below here.
def main():
    aioros2.run()

if __name__ == "__main__":
    main()
