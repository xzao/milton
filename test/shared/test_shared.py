#
#   test/shared/test_shared.py
#
from shared import util


#
#   test[s]
#
def test_env_default():

    # value
    value = util.env_int('MILTON_TEST_UNSET', 7)

    # assert
    assert value == 7
