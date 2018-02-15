.. _notifications:

Notifications
=============

.. autofunction:: properties.observer

.. autoclass:: properties.listeners_disabled

.. autoclass:: properties.observers_disabled

Linking across Properties/Traitlets
-----------------------------------

Properties has :code:`link` functions similar to those from
`traitlets <http://traitlets.readthedocs.io/en/stable/utils.html#links>`_.
This allows easy connection to IPython widgets and other projects that
build on traitlets.

.. autoclass:: properties.directional_link
    :members: unlink, relink

.. autoclass:: properties.link
    :members: unlink, relink
