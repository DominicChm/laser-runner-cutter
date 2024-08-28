import inspect
import aioros2.patch_import

from aioros2.run import run
from aioros2.directives.start import start

import onode

import onode as node1
import onode as node2

@start
async def node_start():
    print(__name__, onode.v, node1.v, node2.v)
    print("STARTED YEE")


if __name__ == "__main__":
    run()