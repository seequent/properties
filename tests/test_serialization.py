from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest
import warnings

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
            assert not isinstance(
                props.HasProperties.deserialize(hp3_dict), HP3
            )
            assert len(w) > 0
            assert issubclass(w[0].category, RuntimeWarning)

        with warnings.catch_warnings(record=True) as w:
            assert not isinstance(
                props.HasProperties.deserialize(hp3_dict_no_class), HP3
            )
            assert len(w) > 0
            assert issubclass(w[0].category, RuntimeWarning)

        with warnings.catch_warnings(record=True) as w:
            assert not isinstance(
                props.HasProperties.deserialize(
                    hp3_dict_no_class, trusted=True
                ), HP3
            )
            assert len(w) > 0
            assert issubclass(w[0].category, RuntimeWarning)

        assert isinstance(HP3.deserialize(hp3_dict), HP3)
        assert isinstance(HP3.deserialize(hp3_dict_no_class), HP3)
        assert isinstance(props.HasProperties.deserialize(hp3_dict), HP3)


if __name__ == '__main__':
    unittest.main()
