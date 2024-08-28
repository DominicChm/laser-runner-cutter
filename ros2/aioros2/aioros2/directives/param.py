from ._decorators import RosDirective

class RosParam(RosDirective):
    def __init__(self, *args):
        # self._desc = ParameterDescriptor()
        pass


def param(*args, **kwargs):
    return RosParam(*args)
