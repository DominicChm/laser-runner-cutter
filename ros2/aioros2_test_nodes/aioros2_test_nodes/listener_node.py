import aioros2
from std_msgs.msg import Bool, String
from common_interfaces.srv import GetInt32
from . import talker_node

a_topic = aioros2.topic("~/talk", String)

talker = aioros2.use(talker_node)

counter = 0

@aioros2.timer(1, True)
async def t():
    a_topic.pub(data="Hello World!")

@aioros2.service("~/increment", GetInt32)
async def increment():
    global counter

    counter += 1
    return {"data": counter}

@aioros2.subscribe(talker.topic_test)
# Boilerplate below here.
def main():
    aioros2.run()

if __name__ == "__main__":
    main()
