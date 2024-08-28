import pytest
from aioros2.deferrable import Deferrable, resolve_deferrable

def setup_deferrable():
    deferrable = Deferrable()

    class _Obj:
        a = "test"

    class Obj:
        a = "string!"
        b = "Another!"
        c = 5
        d = _Obj()

    return deferrable, Obj()

def test_preres_access():
    d, o = setup_deferrable()

    with pytest.raises(ValueError):
        d.d = 5

def test_resolution_on_value():
    d, o = setup_deferrable()

    with pytest.raises(ValueError):
        resolve_deferrable(d.a, {})

def test_basic():
    d, o = setup_deferrable()

    da = d.a
    db = d.b
    dc = d.c
    dda = d.d.a

    resolve_deferrable(d, o)

    assert d.b == "Another!"
    assert d.a == "string!"
    assert d.c == 5

    # Check basic equalities
    assert d.b == db
    assert d.a == da
    assert d.c == dc

    # Check arithmatic
    assert dc > 1
    assert dc < 7
    assert dc <= 5
    assert dc >= 5
    assert dc != 6

    # Check nested object access
    assert d.d.a == dda


def test_subclassing():
    class Obj:
        a = "string!"
        b = "Another!"
        c = 5

    class ObjAccessor(Deferrable):
        def __init__(self) -> None:
            self.module_val = 5

            super().__init__()

    o = ObjAccessor()

    oa = o.a

    with pytest.raises(ValueError):
        o.a = "test"

    resolve_deferrable(o, Obj())

    assert oa == "string!"