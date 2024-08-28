@dataclass
class GenericParams:
    generic_one: str = "test1"
    a_test: str = "test2"

# Executable to call to launch this node (defined in `setup.py`)
@node("amiga_control_node")
class AmigaControlNode:
    generic_params = params(GenericParams)

    dependant_node_1: "circular_node.CircularNode" = import_node(circular_node)
    
    my_topic = topic("~/atopic", String, 10)

    @subscribe(my_topic)
    async def on_my_topic(self, data):
        # ...

    @subscribe(dependant_node_1.a_topic)
    def sub_another_topic(self, data):
        # ...

    # Runs every x seconds.
    @timer(2) 
    async def task(self):
        # ...

    # Service implementation.
    @service("~/set_twist", SetTwist)
    async def set_twist(self, twist) -> bool:
        # ...

    @action("~/test", Run)
    async def act(self, fast) -> AsyncGenerator[int, None]:
        # ...

# Boilerplate below here.
def main():
    serve_nodes(AmigaControlNode())

if __name__ == "__main__":
    main()