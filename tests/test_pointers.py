import unittest, numpy as np, os
import properties


class SomeOptions(properties.PropertyClass):
    color = properties.Color("My color")


class MySurface(properties.PropertyClass):
    opts = properties.Pointer("My options", ptype=SomeOptions, expose=['color'])


class MyShape(properties.PropertyClass):
    surf = properties.Pointer("The surface", ptype=MySurface, required=True)
    sub_surfs = properties.Pointer("The sub-surface", ptype=MySurface, repeated=True)
    opts = properties.Pointer("My other options", ptype=SomeOptions, autogen=True)


class TestBasic(unittest.TestCase):

    def test_resolve(self):
        class MyShapeStrPt(properties.PropertyClass):
            surf = properties.Pointer("The surface", ptype='MySurface', required=True)
            sub_surfs = properties.Pointer("The sub-surface", ptype='MySurface', repeated=True)
            opts = properties.Pointer("My other options", ptype=SomeOptions, autogen=True)

        shp = MyShapeStrPt()
        sfc = MySurface()
        self.assertRaises(AttributeError, lambda: setattr(shp, 'surf', sfc))
        properties.Pointer.resolve()
        setattr(shp, 'surf', sfc)
        assert shp.surf is sfc
        assert shp.surf is shp.surf

    def test_expose(self):
        opts = SomeOptions()
        sfc = MySurface(opts=opts)
        assert sfc.color is sfc.opts.color
        assert opts.color is sfc.color


    def test_autogen(self):
        shp = MyShape()
        sfc = MySurface()
        shp.surf = sfc
        assert getattr(shp, 'opts', None) is not None
        assert isinstance(shp.opts, SomeOptions)
        assert getattr(sfc, 'opts', None) is None

    def test_parent_child(self):
        class MyPossiblyEmptyShape(properties.PropertyClass):
            sub_surfs = properties.Pointer("The sub-surface", ptype='MySurfaceWithParent', repeated=True)
            opts = properties.Pointer("My other options", ptype='SomeOptions', autogen=True)


        class MySurfaceWithParent(properties.PropertyClass):
            parent = properties.Pointer("Parent Shape", ptype='MyPossiblyEmptyShape', required=True)

            def __init__(self, parent=None, **kwargs):
                if parent is None:
                    raise TypeError('You must provide parent')
                self.parent = parent
                self.parent.sub_surfs += [self]
                super(MySurfaceWithParent, self).__init__(**kwargs)

        properties.Pointer.resolve()
        P = MyPossiblyEmptyShape()
        self.assertRaises(TypeError, lambda: MySurfaceWithParent())
        S0 = MySurfaceWithParent(P)
        S1 = MySurfaceWithParent(P)
        S2 = MySurfaceWithParent(P)

        assert P.sub_surfs == P.sub_surfs
        assert len(P.sub_surfs) == 3
        assert P.sub_surfs[0] is P.sub_surfs[0]
        assert P.sub_surfs[0] is S0
        assert P.sub_surfs[1] is S1
        assert P.sub_surfs[2] is S2

        P.validate()





if __name__ == '__main__':
    unittest.main()
