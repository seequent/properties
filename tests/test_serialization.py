from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest

import numpy as np

import properties


class HP1(properties.HasProperties):
    a = properties.Integer('int a')


class HP2(properties.HasProperties):
    inst1 = properties.Instance('b', HP1)


class HP3(properties.HasProperties):
    inst2 = properties.Instance('c', HP2)


class TestSerialization(unittest.TestCase):

    def test_pickle(self):
        hp1 = HP1(a=10)
        hp2 = HP2(inst1=hp1)
        hp3 = HP3(inst2=hp2)

        hp3_copy = pickle.loads(pickle.dumps(hp3))
        assert isinstance(hp3_copy, HP3)
        assert isinstance(hp3_copy.inst2, HP2)
        assert isinstance(hp3_copy.inst2.inst1, HP1)
        assert hp3_copy.inst2.inst1.a == 10

    def test_serialize(self):
        hp1 = HP1(a=10)
        hp2 = HP2(inst1=hp1)
        hp3 = HP3(inst2=hp2)

        hp3_dict = {
            '__class__': 'HP3',
            'inst2': {
                '__class__': 'HP2',
                'inst1': {
                    '__class__': 'HP1',
                    'a': 10,
                },
            },
        }
        hp3_dict_no_class = {
            'inst2': {
                'inst1': {
                    'a': 10,
                },
            },
        }

        assert hp3.serialize() == hp3_dict
        assert hp3.serialize(include_class=False) == hp3_dict_no_class

        assert not isinstance(
            properties.HasProperties.deserialize(hp3_dict), HP3
        )
        assert not isinstance(
            properties.HasProperties.deserialize(hp3_dict_no_class), HP3
        )
        assert not isinstance(
            properties.HasProperties.deserialize(
                hp3_dict_no_class, trusted=True
            ), HP3
        )
        assert isinstance(properties.HasProperties.deserialize(
            {'__class__': 'HP9'}, trusted=True
        ), properties.HasProperties)

        assert isinstance(HP3.deserialize(hp3_dict), HP3)
        assert isinstance(HP3.deserialize(hp3_dict_no_class), HP3)
        assert isinstance(
            properties.HasProperties.deserialize(hp3_dict, trusted=True), HP3
        )

        with self.assertRaises(ValueError):
            HP1.deserialize(5)

        with self.assertRaises(ValueError):
            properties.HasProperties.deserialize(hp3_dict, strict=True)
        assert isinstance(
            HP3.deserialize(hp3_dict, strict=True), HP3
        )
        hp3_extra = {
            '__class__': 'HP3',
            'inst2': {
                '__class__': 'HP2',
                'inst1': {
                    '__class__': 'HP1',
                    'a': 10,
                }
            },
            'b': 1,
        }
        with self.assertRaises(ValueError):
            HP3.deserialize(hp3_extra, strict=True)
        assert isinstance(HP3.deserialize({}), HP3)
        with self.assertRaises(properties.ValidationError):
            HP3.deserialize({}).validate()
        with self.assertRaises(properties.ValidationError):
            HP3.deserialize({}, assert_valid=True)

        hp3_incomplete = {
            '__class__': 'HP3',
            'inst2': {
                '__class__': 'HP2',
                'inst1': {
                    '__class__': 'HP1',
                }
            }
        }

        assert isinstance(HP3.deserialize(hp3_incomplete, strict=True), HP3)
        with self.assertRaises(properties.ValidationError):
            HP3.deserialize(hp3_incomplete, assert_valid=True)

        hp3_subextra = {
            '__class__': 'HP3',
            'inst2': {
                '__class__': 'HP2',
                'inst1': {
                    '__class__': 'HP1',
                    'a': 10,
                    'b': 2,
                }
            }
        }

        assert isinstance(HP3.deserialize(hp3_subextra, assert_valid=True), HP3)
        with self.assertRaises(ValueError):
            HP3.deserialize(hp3_subextra, strict=True)

        class Invalid(properties.HasProperties):

            def validate(self):
                return False

        assert isinstance(Invalid.deserialize({}), Invalid)
        with self.assertRaises(properties.ValidationError):
            Invalid.deserialize({}, assert_valid=True)

        with self.assertRaises(ValueError):
            HP3.deserialize(hp3_dict, _instance=Invalid())


    def test_immutable_serial(self):

        class UidModel(properties.HasProperties):
            uid = properties.Uuid('unique id')

        um1 = UidModel()
        um2 = UidModel.deserialize(um1.serialize())
        assert properties.equal(um1, um2)

    def test_none_serial(self):

        class ManyProperties(properties.HasProperties):
            mystr = properties.String(
                'my string',
                required=False,
            )
            myarr = properties.Array(
                'my array',
                required=False,
            )
            myinst = properties.Instance(
                'my HP1',
                instance_class=HP1,
                required=False,
            )
            mylist = properties.List(
                'my list of HP1',
                prop=HP1,
                required=False,
                default=properties.utils.undefined
            )
            myunion = properties.Union(
                'string or HP1',
                props=(HP1, properties.String('')),
                required=False,
            )

        many = ManyProperties()
        assert many.serialize(include_class=False) == {}


    def test_serializer(self):

        with self.assertRaises(TypeError):
            properties.GettableProperty('bad serial', serializer=5)

        with self.assertRaises(TypeError):
            properties.GettableProperty('bad deserial', deserializer=5)

        def reverse(value):
            return ''.join(v for v in value[::-1])

        def to_string(value):
            return ', '.join(v for v in value.astype(str))

        def from_string(value):
            return np.array(value.split(', ')).astype(int)

        def serialize_a_only(value):
            return value.a

        def deserialize_from_a(value):
            return HP1(a=value)

        def sum_of_a(value):
            return sum(inst.a for inst in value)

        def from_sum(value):
            return [HP1(a=value)]

        def just_the_classname(value):
            return value.__class__.__name__


        class ManyProperties(properties.HasProperties):
            mystr = properties.String(
                'my string',
                serializer=reverse,
                deserializer=reverse,
            )
            myarr = properties.Array(
                'my array',
                serializer=to_string,
                deserializer=from_string,
            )
            myinst = properties.Instance(
                'my HP1',
                instance_class=HP1,
                serializer=serialize_a_only,
                deserializer=deserialize_from_a,
            )
            mylist = properties.List(
                'my list of HP1',
                prop=HP1,
                serializer=sum_of_a,
                deserializer=from_sum,
            )
            myunion = properties.Union(
                'string or HP1',
                props=(HP1, properties.String('')),
                serializer=just_the_classname,
                deserializer=reverse,
            )

        many = ManyProperties(
            mystr='abcd',
            myarr=[1, 2, 3],
            myinst=HP1(a=10),
            mylist=[HP1(a=1), HP1(a=2), HP1(a=3)],
            myunion=HP1(a=10)
        )

        many_serialized = {
            'mystr': 'dcba',
            'myarr': '1, 2, 3',
            'myinst': 10,
            'mylist': 6,
            'myunion': 'HP1'
        }

        assert many.serialize(include_class=False) == many_serialized

        many = ManyProperties.deserialize(many_serialized)
        assert many.mystr == 'abcd'
        assert isinstance(many.myarr, np.ndarray)
        assert np.all(many.myarr == [1, 2, 3])
        assert isinstance(many.myinst, HP1)
        assert many.myinst.a == 10
        assert isinstance(many.mylist, list)
        assert len(many.mylist) == 1
        assert isinstance(many.mylist[0], HP1)
        assert many.mylist[0].a == 6
        assert many.myunion == '1PH'

        assert isinstance(ManyProperties.deserialize({'mystr': 'hi'}), ManyProperties)


        def kwarg_multiplier(value, **kwargs):
            mult = kwargs.get('mult', 1)
            return value * mult

        def kwarg_divider(value, **kwargs):
            mult = kwargs.get('mult', 1)
            return value / mult

        class HasInt(properties.HasProperties):

            my_int = properties.Integer(
                'Integer serialized as mult',
                serializer=kwarg_multiplier,
                deserializer=kwarg_divider,
            )

        hi = HasInt(my_int=5)

        hi_ser = hi.serialize()
        assert hi_ser['my_int'] == 5
        hi_copy = HasInt.deserialize(hi_ser)
        assert hi_copy.my_int == 5

        hi_ser = hi.serialize(mult=2)
        assert hi_ser['my_int'] == 10
        hi_copy = HasInt.deserialize(hi_ser, mult=2)
        assert hi_copy.my_int == 5


    def test_dynamic_serial(self):

        class DynamicModel(properties.HasProperties):
            a = properties.Integer('')
            b = properties.Renamed('a')

            @properties.Integer('')
            def c(self):
                return self.a

        dm1 = DynamicModel()
        dm1.a = 5
        assert dm1.b == 5
        assert dm1.c == 5

        dm_save_dynamic = dm1.serialize(save_dynamic=True)
        dm_skip_dynamic = dm1.serialize()

        assert dm_skip_dynamic == {'__class__': 'DynamicModel', 'a': 5}
        assert dm_save_dynamic == {'__class__': 'DynamicModel',
                                  'a': 5, 'b': 5, 'c': 5}


        dm2 = DynamicModel.deserialize(dm_skip_dynamic)
        assert properties.equal(dm1, dm2)
        dm3 = DynamicModel.deserialize(dm_save_dynamic)
        assert properties.equal(dm1, dm3)


if __name__ == '__main__':
    unittest.main()
