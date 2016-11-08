from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest
import warnings

import numpy as np

import properties as props


class HP1(props.HasProperties):
    a = props.Integer('int a')


class HP2(props.HasProperties):
    inst1 = props.Instance('b', HP1)


class HP3(props.HasProperties):
    inst2 = props.Instance('c', HP2)


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
                    'a': 10
                }
            }
        }
        hp3_dict_no_class = {
            'inst2': {
                'inst1': {
                    'a': 10
                }
            }
        }

        assert hp3.serialize() == hp3_dict
        assert hp3.serialize(include_class=False) == hp3_dict_no_class

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            assert not isinstance(
                props.HasProperties.deserialize(hp3_dict), HP3
            )
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert not isinstance(
                props.HasProperties.deserialize(hp3_dict_no_class), HP3
            )
            assert len(w) == 2
            assert issubclass(w[1].category, RuntimeWarning)
            assert not isinstance(
                props.HasProperties.deserialize(
                    hp3_dict_no_class, trusted=True
                ), HP3
            )
            assert len(w) == 3
            assert issubclass(w[2].category, RuntimeWarning)
            assert isinstance(props.HasProperties.deserialize(
                {'__class__': 'HP9'}, trusted=True
            ), props.HasProperties)
            assert len(w) == 4
            assert issubclass(w[3].category, RuntimeWarning)

        assert isinstance(HP3.deserialize(hp3_dict), HP3)
        assert isinstance(HP3.deserialize(hp3_dict_no_class), HP3)
        assert isinstance(
            props.HasProperties.deserialize(hp3_dict, trusted=True), HP3
        )

    def test_none_serial(self):

        class ManyProperties(props.HasProperties):
            mystr = props.String(
                'my string',
                required=False,
            )
            myarr = props.Array(
                'my array',
                required=False,
            )
            myinst = props.Instance(
                'my HP1',
                instance_class=HP1,
                required=False,
            )
            mylist = props.List(
                'my list of HP1',
                prop=HP1,
                required=False,
                default=props.utils.undefined
            )
            myunion = props.Union(
                'string or HP1',
                props=(HP1, props.String('')),
                required=False,
            )

        many = ManyProperties()
        assert many.serialize(include_class=False) == {}


    def test_serializer(self):

        with self.assertRaises(TypeError):
            props.GettableProperty('bad serial', serializer=5)

        with self.assertRaises(TypeError):
            props.GettableProperty('bad deserial', deserializer=5)

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



        class ManyProperties(props.HasProperties):
            mystr = props.String(
                'my string',
                serializer=reverse,
                deserializer=reverse,
            )
            myarr = props.Array(
                'my array',
                serializer=to_string,
                deserializer=from_string,
            )
            myinst = props.Instance(
                'my HP1',
                instance_class=HP1,
                serializer=serialize_a_only,
                deserializer=deserialize_from_a,
            )
            mylist = props.List(
                'my list of HP1',
                prop=HP1,
                serializer=sum_of_a,
                deserializer=from_sum,
            )
            myunion = props.Union(
                'string or HP1',
                props=(HP1, props.String('')),
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


if __name__ == '__main__':
    unittest.main()
