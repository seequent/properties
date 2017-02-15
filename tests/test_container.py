from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestContainer(unittest.TestCase):

    def test_tuple(self):

        with self.assertRaises(TypeError):
            properties.Tuple('bad string tuple', prop=str)
        with self.assertRaises(TypeError):
            properties.Tuple('bad max', properties.Integer(''),
                            max_length=-10)
        with self.assertRaises(TypeError):
            properties.Tuple('bad max', properties.Integer(''),
                            max_length='ten')
        with self.assertRaises(TypeError):
            mytuple = properties.Tuple('bad max', properties.Integer(''),
                                     min_length=20)
            mytuple.max_length = 10
        with self.assertRaises(TypeError):
            properties.Tuple('bad min', properties.Integer(''),
                            min_length=-10)
        with self.assertRaises(TypeError):
            properties.Tuple('bad min', properties.Integer(''),
                            min_length='ten')
        with self.assertRaises(TypeError):
            mytuple = properties.Tuple('bad min', properties.Integer(''),
                                     max_length=10)
            mytuple.min_length = 20
        with self.assertRaises(AttributeError):
            properties.Tuple('bad observe', properties.Integer(''),
                            observe_mutations=5)
        with self.assertRaises(TypeError):
            properties.Tuple('bad coerce', properties.Integer(''),
                            coerce=5)

        class HasPropsDummy(properties.HasProperties):
            pass

        mytuple = properties.Tuple('dummy has properties tuple',
                                 prop=HasPropsDummy)
        assert isinstance(mytuple.prop, properties.Instance)
        assert mytuple.prop.instance_class is HasPropsDummy

        class HasDummyTuple(properties.HasProperties):
            mytuple = properties.Tuple('dummy has properties tuple',
                                     prop=HasPropsDummy)

        assert HasDummyTuple()._props['mytuple'].name == 'mytuple'
        assert HasDummyTuple()._props['mytuple'].prop.name == 'mytuple'

        class HasIntTuple(properties.HasProperties):
            aaa = properties.Tuple('tuple of ints', properties.Integer(''))

        li = HasIntTuple()
        li.aaa = (1, 2, 3)
        with self.assertRaises(ValueError):
            li.aaa = [1, 2, 3]
        li.aaa = (1., 2., 3.)
        with self.assertRaises(ValueError):
            li.aaa = 4
        with self.assertRaises(ValueError):
            li.aaa = ('a', 'b', 'c')

        li1 = HasIntTuple()
        li2 = HasIntTuple()
        assert li1.aaa == li2.aaa
        assert li1.aaa is li2.aaa
        li1.aaa += (1,)
        assert li1.aaa is not li2.aaa

        class HasCoercedIntTuple(properties.HasProperties):
            aaa = properties.Tuple('tuple of ints', properties.Integer(''),
                                   coerce=True)

        li = HasCoercedIntTuple()
        li.aaa = 1
        assert li.aaa == (1,)
        li.aaa = [1, 2, 3]
        assert li.aaa == (1, 2, 3)
        li.aaa = {1, 2, 3}
        assert isinstance(li.aaa, tuple)
        assert all(val in li.aaa for val in [1, 2, 3])

        class HasConstrianedTuple(properties.HasProperties):
            aaa = properties.Tuple('tuple of ints', properties.Integer(''),
                                  min_length=2)

        li = HasConstrianedTuple()
        li.aaa = (1, 2, 3)
        li.validate()
        li.aaa = (1,)
        with self.assertRaises(ValueError):
            li.validate()

        class HasConstrianedTuple(properties.HasProperties):
            aaa = properties.Tuple('tuple of ints', properties.Integer(''),
                                  max_length=2)

        li = HasConstrianedTuple()
        li.aaa = (1, 2)
        li.validate()
        li.aaa = (1, 2, 3, 4, 5)
        with self.assertRaises(ValueError):
            li.validate()

        class HasColorTuple(properties.HasProperties):
            ccc = properties.Tuple('tuple of colors', properties.Color(''))

        li = HasColorTuple()
        li.ccc = ('red', '#00FF00')
        assert li.ccc[0] == (255, 0, 0)
        assert li.ccc[1] == (0, 255, 0)

        numtuple = (1, 2, 3, 4)
        assert properties.Tuple.to_json(numtuple) == list(numtuple)
        assert properties.Tuple.from_json(list(numtuple)) == numtuple

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a', required=True)

        assert properties.Tuple.to_json(
            (HasIntA(a=5), HasIntA(a=10))
        ) == [{'__class__': 'HasIntA', 'a': 5},
              {'__class__': 'HasIntA', 'a': 10}]

        assert li.serialize(include_class=False) == {
            'ccc': [[255, 0, 0], [0, 255, 0]]
        }

        class HasIntATuple(properties.HasProperties):
            mytuple = properties.Tuple('tuple of HasIntA', HasIntA)

        deser_tuple = HasIntATuple.deserialize(
            {'mytuple': [{'a': 0}, {'a': 10}, {'a': 100}]}
        ).mytuple
        assert isinstance(deser_tuple, tuple)
        assert len(deser_tuple) == 3
        assert isinstance(deser_tuple[0], HasIntA) and deser_tuple[0].a == 0
        assert isinstance(deser_tuple[1], HasIntA) and deser_tuple[1].a == 10
        assert isinstance(deser_tuple[2], HasIntA) and deser_tuple[2].a == 100

        class HasOptionalTuple(properties.HasProperties):
            mytuple = properties.Tuple('', properties.Bool(''), required=False)

        hol = HasOptionalTuple()
        hol.validate()

        assert HasIntATuple._props['mytuple'].deserialize(None) is None

        assert properties.Tuple(
            '', properties.Instance('', HasIntA)
        ).equal(
            (HasIntA(a=1), HasIntA(a=2)), (HasIntA(a=1), HasIntA(a=2))
        )
        assert not properties.Tuple(
            '', properties.Instance('', HasIntA)
        ).equal(
            (HasIntA(a=1), HasIntA(a=2)),
            (HasIntA(a=1), HasIntA(a=2), HasIntA(a=3))
        )
        assert not properties.Tuple(
            '', properties.Instance('', HasIntA)
        ).equal(
            (HasIntA(a=1), HasIntA(a=2)), (HasIntA(a=1), HasIntA(a=3))
        )
        assert not properties.Tuple('', properties.Integer('')).equal(5, 5)

    def test_list(self):
        self._test_list(True)
        self._test_list(False)

    def _test_list(self, om):

        with self.assertRaises(TypeError):
            properties.List('bad string list', prop=str)
        with self.assertRaises(TypeError):
            properties.List('bad max', properties.Integer(''),
                            max_length=-10)
        with self.assertRaises(TypeError):
            properties.List('bad max', properties.Integer(''),
                            max_length='ten')
        with self.assertRaises(TypeError):
            mylist = properties.List('bad max', properties.Integer(''),
                                     min_length=20)
            mylist.max_length = 10
        with self.assertRaises(TypeError):
            properties.List('bad min', properties.Integer(''),
                            min_length=-10)
        with self.assertRaises(TypeError):
            properties.List('bad min', properties.Integer(''),
                            min_length='ten')
        with self.assertRaises(TypeError):
            mylist = properties.List('bad min', properties.Integer(''),
                                     max_length=10)
            mylist.min_length = 20
        with self.assertRaises(TypeError):
            properties.List('bad observe', properties.Integer(''),
                            observe_mutations=5)
        with self.assertRaises(TypeError):
            properties.List('bad coerce', properties.Integer(''),
                            coerce=5)

        class HasPropsDummy(properties.HasProperties):
            pass

        mylist = properties.List('dummy has properties list',
                                 prop=HasPropsDummy, observe_mutations=om)
        assert isinstance(mylist.prop, properties.Instance)
        assert mylist.prop.instance_class is HasPropsDummy

        class HasDummyList(properties.HasProperties):
            mylist = properties.List('dummy has properties list',
                                     prop=HasPropsDummy, observe_mutations=om)

        assert HasDummyList()._props['mylist'].name == 'mylist'
        assert HasDummyList()._props['mylist'].prop.name == 'mylist'

        class HasIntList(properties.HasProperties):
            aaa = properties.List('list of ints', properties.Integer(''),
                                  observe_mutations=om)

        li = HasIntList()
        li.aaa = [1, 2, 3]
        with self.assertRaises(ValueError):
            li.aaa = (1, 2, 3)
        li.aaa = [1., 2., 3.]
        with self.assertRaises(ValueError):
            li.aaa = 4
        with self.assertRaises(ValueError):
            li.aaa = ['a', 'b', 'c']

        li1 = HasIntList()
        li2 = HasIntList()
        assert li1.aaa == li2.aaa
        assert li1.aaa is not li2.aaa

        class HasCoercedIntList(properties.HasProperties):
            aaa = properties.List('list of ints', properties.Integer(''),
                                  observe_mutations=om, coerce=True)

        li = HasCoercedIntList()
        li.aaa = 1
        assert li.aaa == [1]
        li.aaa = (1, 2, 3)
        assert li.aaa == [1, 2, 3]
        li.aaa = {1, 2, 3}
        assert isinstance(li.aaa, list)
        assert all(val in li.aaa for val in [1, 2, 3])

        class HasConstrianedList(properties.HasProperties):
            aaa = properties.List('list of ints', properties.Integer(''),
                                  min_length=2, observe_mutations=om)

        li = HasConstrianedList()
        li.aaa = [1, 2, 3]
        li.validate()
        li.aaa = [1]
        with self.assertRaises(ValueError):
            li.validate()

        class HasConstrianedList(properties.HasProperties):
            aaa = properties.List('list of ints', properties.Integer(''),
                                  max_length=2, observe_mutations=om)

        li = HasConstrianedList()
        li.aaa = [1, 2]
        li.validate()
        li.aaa = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            li.validate()

        class HasColorList(properties.HasProperties):
            ccc = properties.List('list of colors', properties.Color(''),
                                  observe_mutations=om)

        li = HasColorList()
        li.ccc = ['red', '#00FF00']
        assert li.ccc[0] == (255, 0, 0)
        assert li.ccc[1] == (0, 255, 0)

        numlist = [1, 2, 3, 4]
        assert properties.List.to_json(numlist) == numlist
        assert properties.List.to_json(numlist) is not numlist
        assert properties.List.from_json(numlist) == numlist
        assert properties.List.from_json(numlist) is not numlist

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a', required=True)

        assert properties.List.to_json(
            [HasIntA(a=5), HasIntA(a=10)]
        ) == [{'__class__': 'HasIntA', 'a': 5},
              {'__class__': 'HasIntA', 'a': 10}]

        assert li.serialize(include_class=False) == {
            'ccc': [[255, 0, 0], [0, 255, 0]]
        }

        class HasIntAList(properties.HasProperties):
            mylist = properties.List('list of HasIntA', HasIntA,
                                     observe_mutations=om)

        deser_list = HasIntAList.deserialize(
            {'mylist': [{'a': 0}, {'a': 10}, {'a': 100}]}
        ).mylist
        assert isinstance(deser_list, list)
        assert len(deser_list) == 3
        assert isinstance(deser_list[0], HasIntA) and deser_list[0].a == 0
        assert isinstance(deser_list[1], HasIntA) and deser_list[1].a == 10
        assert isinstance(deser_list[2], HasIntA) and deser_list[2].a == 100

        class HasOptionalList(properties.HasProperties):
            mylist = properties.List('', properties.Bool(''), required=False,
                                     observe_mutations=om)

        hol = HasOptionalList()
        hol.validate()

        assert HasIntAList._props['mylist'].deserialize(None) is None

        assert properties.List(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            [HasIntA(a=1), HasIntA(a=2)], [HasIntA(a=1), HasIntA(a=2)]
        )
        assert not properties.List(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            [HasIntA(a=1), HasIntA(a=2)],
            [HasIntA(a=1), HasIntA(a=2), HasIntA(a=3)]
        )
        assert not properties.List(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            [HasIntA(a=1), HasIntA(a=2)], [HasIntA(a=1), HasIntA(a=3)]
        )
        assert not properties.List('', properties.Integer(''),
                                   observe_mutations=om).equal(5, 5)

    def test_set(self):
        self._test_set(True)
        self._test_set(False)

    def _test_set(self, om):

        with self.assertRaises(TypeError):
            properties.Set('bad string set', prop=str)
        with self.assertRaises(TypeError):
            properties.Set('bad max', properties.Integer(''),
                            max_length=-10)
        with self.assertRaises(TypeError):
            properties.Set('bad max', properties.Integer(''),
                            max_length='ten')
        with self.assertRaises(TypeError):
            myset = properties.Set('bad max', properties.Integer(''),
                                     min_length=20)
            myset.max_length = 10
        with self.assertRaises(TypeError):
            properties.Set('bad min', properties.Integer(''),
                            min_length=-10)
        with self.assertRaises(TypeError):
            properties.Set('bad min', properties.Integer(''),
                            min_length='ten')
        with self.assertRaises(TypeError):
            myset = properties.Set('bad min', properties.Integer(''),
                                     max_length=10)
            myset.min_length = 20
        with self.assertRaises(TypeError):
            properties.Set('bad observe', properties.Integer(''),
                            observe_mutations=5)
        with self.assertRaises(TypeError):
            properties.Set('bad coerce', properties.Integer(''),
                            coerce=5)

        class HasPropsDummy(properties.HasProperties):
            pass

        myset = properties.Set('dummy has properties set',
                                 prop=HasPropsDummy, observe_mutations=om)
        assert isinstance(myset.prop, properties.Instance)
        assert myset.prop.instance_class is HasPropsDummy

        class HasDummySet(properties.HasProperties):
            myset = properties.Set('dummy has properties set',
                                     prop=HasPropsDummy, observe_mutations=om)

        assert HasDummySet()._props['myset'].name == 'myset'
        assert HasDummySet()._props['myset'].prop.name == 'myset'

        class HasIntSet(properties.HasProperties):
            aaa = properties.Set('set of ints', properties.Integer(''),
                                  observe_mutations=om)

        li = HasIntSet()
        li.aaa = {1, 2, 3}
        with self.assertRaises(ValueError):
            li.aaa = (1, 2, 3)
        li.aaa = {1., 2., 3.}
        with self.assertRaises(ValueError):
            li.aaa = 4
        with self.assertRaises(ValueError):
            li.aaa = {'a', 'b', 'c'}

        li1 = HasIntSet()
        li2 = HasIntSet()
        assert li1.aaa == li2.aaa
        assert li1.aaa is not li2.aaa

        class HasCoercedIntSet(properties.HasProperties):
            aaa = properties.Set('set of ints', properties.Integer(''),
                                 observe_mutations=om, coerce=True)

        li = HasCoercedIntSet()
        li.aaa = 1
        assert li.aaa == {1}
        li.aaa = [1, 2, 3]
        assert li.aaa == {1, 2, 3}
        li.aaa = (1, 2, 3)
        assert li.aaa == {1, 2, 3}

        class HasConstrianedSet(properties.HasProperties):
            aaa = properties.Set('set of ints', properties.Integer(''),
                                  min_length=2, observe_mutations=om)

        li = HasConstrianedSet()
        li.aaa = {1, 2, 3}
        li.validate()
        li.aaa = {1}
        with self.assertRaises(ValueError):
            li.validate()

        class HasConstrianedSet(properties.HasProperties):
            aaa = properties.Set('set of ints', properties.Integer(''),
                                  max_length=2, observe_mutations=om)

        li = HasConstrianedSet()
        li.aaa = {1, 2}
        li.validate()
        li.aaa = {1, 2, 3, 4, 5}
        with self.assertRaises(ValueError):
            li.validate()

        class HasColorSet(properties.HasProperties):
            ccc = properties.Set('set of colors', properties.Color(''),
                                  observe_mutations=om)

        li = HasColorSet()
        li.ccc = {'red', '#00FF00'}
        assert li.ccc == {(255, 0, 0), (0, 255, 0)}

        numset = {1, 2, 3, 4}
        assert properties.Set.to_json(numset) == list(numset)
        assert properties.Set.from_json(list(numset)) == numset
        assert properties.Set.from_json(list(numset)) is not numset

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a', required=True)

        assert (
            properties.Set.to_json(
                {HasIntA(a=5), HasIntA(a=10)}
            ) == [{'__class__': 'HasIntA', 'a': 5},
                  {'__class__': 'HasIntA', 'a': 10}] or
            properties.Set.to_json(
                {HasIntA(a=5), HasIntA(a=10)}
            ) == [{'__class__': 'HasIntA', 'a': 10},
                  {'__class__': 'HasIntA', 'a': 5}]
        )

        assert li.serialize(include_class=False) == {
            'ccc': [[255, 0, 0], [0, 255, 0]]
        } or li.serialize(include_class=False) == {
            'ccc': [[0, 255, 0], [255, 0, 0]]
        }

        class HasIntASet(properties.HasProperties):
            myset = properties.Set('set of HasIntA', HasIntA,
                                     observe_mutations=om)

        deser_set = HasIntASet.deserialize(
            {'myset': [{'a': 0}, {'a': 10}, {'a': 100}]}
        ).myset
        assert isinstance(deser_set, set)
        assert len(deser_set) == 3
        assert all(isinstance(val, HasIntA) for val in deser_set)
        assert {val.a for val in deser_set} == {0, 10, 100}

        class HasOptionalSet(properties.HasProperties):
            myset = properties.Set('', properties.Bool(''), required=False,
                                     observe_mutations=om)

        hol = HasOptionalSet()
        hol.validate()

        assert HasIntASet._props['myset'].deserialize(None) is None

        assert properties.Set(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            {HasIntA(a=1), HasIntA(a=2)}, {HasIntA(a=1), HasIntA(a=2)}
        )
        assert not properties.Set(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            {HasIntA(a=1), HasIntA(a=2)},
            {HasIntA(a=1), HasIntA(a=2), HasIntA(a=3)}
        )
        assert not properties.Set(
            '', properties.Instance('', HasIntA), observe_mutations=om
        ).equal(
            {HasIntA(a=1), HasIntA(a=2)}, {HasIntA(a=1), HasIntA(a=3)}
        )
        assert not properties.Set('', properties.Integer(''),
                                   observe_mutations=om).equal(5, 5)

    def test_basic_vs_advanced_list(self):

        class HasLists(properties.HasProperties):
            basic = properties.List('', properties.Integer(''))
            advanced = properties.List('', properties.Integer(''),
                                       observe_mutations=True)

            def __init__(self, **kwargs):
                self._basic_tic = 0
                self._advanced_tic = 0

            @properties.validator('basic')
            def _basic_val(self, change):
                self._basic_tic += 1

            @properties.validator('advanced')
            def _advanced_val(self, change):
                self._advanced_tic += 1

        hl = HasLists()
        hl.basic = [1, 2, 3]
        hl.advanced = [1, 2, 3]

        assert hl._basic_tic == 1
        assert hl._advanced_tic == 1

        temp = hl.basic
        temp[0] = 10
        assert hl.basic == [10, 2, 3]
        assert hl._basic_tic == 1

        temp = hl.advanced
        temp[0] = 10
        assert hl.advanced == [10, 2, 3]
        assert hl._advanced_tic == 2

        hl.advanced = [1, 2, 3]
        temp[1] = 20
        assert hl.advanced == [1, 2, 3]
        assert hl._advanced_tic == 3

        hl.basic.append(5)
        assert hl.basic == [10, 2, 3, 5]
        assert hl._basic_tic == 1
        hl.advanced.append(5)
        assert hl.advanced == [1, 2, 3, 5]
        assert hl._advanced_tic == 4

        hl.basic.extend([6, 7])
        assert hl.basic == [10, 2, 3, 5, 6, 7]
        assert hl._basic_tic == 1
        hl.advanced.extend([6, 7])
        assert hl.advanced == [1, 2, 3, 5, 6, 7]
        assert hl._advanced_tic == 5

        hl.basic.insert(0, 1)
        assert hl.basic == [1, 10, 2, 3, 5, 6, 7]
        assert hl._basic_tic == 1
        hl.advanced.insert(0, 1)
        assert hl.advanced == [1, 1, 2, 3, 5, 6, 7]
        assert hl._advanced_tic == 6

        assert hl.basic.pop() == 7
        assert hl.basic == [1, 10, 2, 3, 5, 6]
        assert hl._basic_tic == 1
        assert hl.advanced.pop() == 7
        assert hl.advanced == [1, 1, 2, 3, 5, 6]
        assert hl._advanced_tic == 7

        hl.basic.remove(5)
        assert hl.basic == [1, 10, 2, 3, 6]
        assert hl._basic_tic == 1
        hl.advanced.remove(5)
        assert hl.advanced == [1, 1, 2, 3, 6]
        assert hl._advanced_tic == 8

        hl.basic.sort()
        assert hl.basic == [1, 2, 3, 6, 10]
        assert hl._basic_tic == 1
        hl.advanced.sort()
        assert hl.advanced == [1, 1, 2, 3, 6]
        assert hl._advanced_tic == 9

        hl.basic.reverse()
        assert hl.basic == [10, 6, 3, 2, 1]
        assert hl._basic_tic == 1
        hl.advanced.reverse()
        assert hl.advanced == [6, 3, 2, 1, 1]
        assert hl._advanced_tic == 10

        del hl.basic[3]
        assert hl.basic == [10, 6, 3, 1]
        assert hl._basic_tic == 1
        del hl.advanced[3]
        assert hl.advanced == [6, 3, 2, 1]
        assert hl._advanced_tic == 11

        hl.basic[0:2] = [8, 8]
        assert hl.basic == [8, 8, 3, 1]
        assert hl._basic_tic == 1
        hl.advanced[0:2] = [8, 8]
        assert hl.advanced == [8, 8, 2, 1]
        assert hl._advanced_tic == 12

        del hl.basic[0:2]
        assert hl.basic == [3, 1]
        assert hl._basic_tic == 1
        del hl.advanced[0:2]
        assert hl.advanced == [2, 1]
        assert hl._advanced_tic == 13

        hl.basic += [5, 6, 7]
        assert hl.basic == [3, 1, 5, 6, 7]
        assert hl._basic_tic == 2
        hl.advanced += [5, 6, 7]
        assert hl.advanced == [2, 1, 5, 6, 7]
        assert hl._advanced_tic == 14

        hl.basic *= 2
        assert hl.basic == [3, 1, 5, 6, 7, 3, 1, 5, 6, 7]
        assert hl._basic_tic == 3
        hl.advanced *= 2
        assert hl.advanced == [2, 1, 5, 6, 7, 2, 1, 5, 6, 7]
        assert hl._advanced_tic == 15

    def test_basic_vs_advanced_set(self):

        class HasSets(properties.HasProperties):
            basic = properties.Set('', properties.Integer(''))
            advanced = properties.Set('', properties.Integer(''),
                                       observe_mutations=True)

            def __init__(self, **kwargs):
                self._basic_tic = 0
                self._advanced_tic = 0

            @properties.validator('basic')
            def _basic_val(self, change):
                self._basic_tic += 1

            @properties.validator('advanced')
            def _advanced_val(self, change):
                self._advanced_tic += 1

        hl = HasSets()
        hl.basic = {1, 2, 3}
        hl.advanced = {1, 2, 3}

        assert hl._basic_tic == 1
        assert hl._advanced_tic == 1

        temp = hl.basic
        temp.add(10)
        assert hl.basic == {1, 2, 3, 10}
        assert hl._basic_tic == 1

        temp = hl.advanced
        temp.add(10)
        assert hl.advanced == {1, 2, 3, 10}
        assert hl._advanced_tic == 2

        hl.advanced = {1, 2, 3}
        temp.add(20)
        assert hl.advanced == {1, 2, 3}
        assert hl._advanced_tic == 3

        hl.basic.clear()
        assert hl.basic == set()
        assert hl._basic_tic == 1
        hl.advanced.clear()
        assert hl.advanced == set()
        assert hl._advanced_tic == 4

        hl.basic.update({6, 7})
        assert hl.basic == {6, 7}
        assert hl._basic_tic == 1
        hl.advanced.update({6, 7})
        assert hl.advanced == {6, 7}
        assert hl._advanced_tic == 5

        hl.basic.difference_update({7})
        assert hl.basic == {6}
        assert hl._basic_tic == 1
        hl.advanced.difference_update({7})
        assert hl.advanced == {6}
        assert hl._advanced_tic == 6

        hl.basic.symmetric_difference_update({7, 8, 9})
        assert hl.basic == {6, 7, 8, 9}
        assert hl._basic_tic == 1
        hl.advanced.symmetric_difference_update({7, 8, 9})
        assert hl.advanced == {6, 7, 8, 9}
        assert hl._advanced_tic == 7

        hl.basic.remove(7)
        assert hl.basic == {6, 8, 9}
        assert hl._basic_tic == 1
        hl.advanced.remove(7)
        assert hl.advanced == {6, 8, 9}
        assert hl._advanced_tic == 8

        hl.basic.discard(7)
        assert hl.basic == {6, 8, 9}
        assert hl._basic_tic == 1
        hl.advanced.discard(7)
        assert hl.advanced == {6, 8, 9}
        assert hl._advanced_tic == 9

        hl.basic.intersection_update({6})
        assert hl.basic == {6}
        assert hl._basic_tic == 1
        hl.advanced.intersection_update({6})
        assert hl.advanced == {6}
        assert hl._advanced_tic == 10

        assert hl.basic.pop() == 6
        assert hl.basic == set()
        assert hl._basic_tic == 1
        assert hl.advanced.pop() == 6
        assert hl.advanced == set()
        assert hl._advanced_tic == 11

        hl.basic |= {1, 2, 3}
        assert hl.basic == {1, 2, 3}
        assert hl._basic_tic == 2
        hl.advanced |= {1, 2, 3}
        assert hl.advanced == {1, 2, 3}
        assert hl._advanced_tic == 12

        hl.basic &= {1, 2, 3}
        assert hl.basic == {1, 2, 3}
        assert hl._basic_tic == 3
        hl.advanced &= {1, 2, 3}
        assert hl.advanced == {1, 2, 3}
        assert hl._advanced_tic == 13

        hl.basic ^= {3, 4, 5}
        assert hl.basic == {1, 2, 4, 5}
        assert hl._basic_tic == 4
        hl.advanced ^= {3, 4, 5}
        assert hl.advanced == {1, 2, 4, 5}
        assert hl._advanced_tic == 14

        hl.basic -= {4, 5}
        assert hl.basic == {1, 2}
        assert hl._basic_tic == 5
        hl.advanced -= {4, 5}
        assert hl.advanced == {1, 2}
        assert hl._advanced_tic == 15


if __name__ == '__main__':
    unittest.main()
