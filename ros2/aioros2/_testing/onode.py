from aioros2.directives.start import start
import random
import sys


v = random.random()

import node as n1

@start
async def node_start():
    print("STARTED other node!", v)