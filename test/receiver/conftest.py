#
#   test/receiver/conftest.py
#
import os
import sys


#
#   var[s]
#
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'receiver'))


#
#   path
#
if SRC not in sys.path:
    sys.path.insert(0, SRC)
