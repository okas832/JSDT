import sys
if sys.version_info[:2] < (3, 7):
    m = "Python 3.7 or later is required for js_mutator (%d.%d detected)."
    raise ImportError(m % sys.version_info[:2])
del sys

import mutator.js_mutator
import mutator.unit_mutator
from mutator.js_mutator import code_mutator