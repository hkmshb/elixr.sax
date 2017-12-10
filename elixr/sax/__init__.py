"""SqlAlchemy eXtension: a toolkit of reusable SQLAlchemy types, data models and 
utility functions encapsulating best practices or exposing convenient facades for
data access and handling.

Copyright (c) 2017, Hazeltek Solutions.
"""

__author__  = 'Hazeltek Solutions'
__version__ = '0.3.1'



# hint: packages are exposed instead of their contents in
# order to ease replacing for meta.BASE and types.UUID
from . import meta, types
from .mixins import (
    IdMixin,
    IdsMixin,
    UUIDMixin,
    IdTimestampMixin,
    TimestampMixin
)
