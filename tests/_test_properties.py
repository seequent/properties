import properties
# import properties_db3
# properties.set_default_backend('db3')


# properties.set_default_backend('traitlets')


# print properties.Integer._backends


# class CoffeeProfile(tr.HasTraits):
#     name = tr.Integer()

class CoffeeProfile(properties.HasProperties):
    name = properties.Integer(
        'What should I call you?',
        required=True
    )
    _REGISTRY = dict()
    # count = properties.Integer(
    #     'number of coffees today'
    # )
    # enough_coffee = properties.Bool(
    #     'Have you had enough coffee today?',
    #     default=False
    # )
    # caffeine_choice = properties.String(
    #     'How do you take your caffeine?',
    #     choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy']
    # )

print CoffeeProfile()._backend


class CoffeeProfile2(CoffeeProfile):
    y = properties.Integer(
        'What should I call you?',
        required=True
    )

    @properties.observe('y')
    def _on_y_change(self, change):
        print('y changed', change)


class CoffeeProfile3(CoffeeProfile):
    x = properties.Integer(
        'What should I call you?',
        required=True
    )


class CoffeeProfile4(CoffeeProfile2, CoffeeProfile3):
    blah = properties.Integer(
        'What should I call you 42?',
        required=True
    )

    @property
    def x(self):
        return 1

    # @properties.observe('x')
    # def _on_x_change(self, change):
    #     print('x changed', change)

# print CoffeeProfile4._backend_class
print CoffeeProfile4._backend_class.__mro__
# print isinstance(CoffeeProfile4._backend_class(), dict)
# print dir(CoffeeProfile4._backend_class())
# print CoffeeProfile4._props['blah'].help
profile = CoffeeProfile4(y=1)

print profile.name
profile.name = False
print profile._backend
print profile.name

print [x for x in dir(profile) if not x.startswith('_')]


print CoffeeProfile._REGISTRY

assert 'x' not in CoffeeProfile4._props

print('hi')
profile.y = 2


def temp(inst, change):
    print('temp', inst, change)

properties.observe(profile, 'y', temp)


profile.y = 3

# profile.name

# print profile._backend.name
