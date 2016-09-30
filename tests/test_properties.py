import properties
# import properties_db3
# properties.set_default_backend('db3')


properties.set_default_backend('traitlets')


# print properties.Integer._backends


# class CoffeeProfile(tr.HasTraits):
#     name = tr.Integer()

class CoffeeProfile(properties.HasProperties('dict')):
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

# profile.name

# print profile._backend.name
