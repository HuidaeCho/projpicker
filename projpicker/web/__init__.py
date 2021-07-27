to_exclude = ['web']

from .web import *

for name in to_exclude:
    del globals()[name]

