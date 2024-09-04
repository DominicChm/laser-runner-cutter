import aioros2
from std_msgs.msg import Bool, String

a_topic = aioros2.topic("~/talk", String)

@aioros2.timer(1, True)
async def t():
    a_topic.pub(data="Hello World!")

# Boilerplate below here.
def main():
    aioros2.run()

if __name__ == "__main__":
    main()
