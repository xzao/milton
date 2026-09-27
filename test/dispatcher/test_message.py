#
#   test/dispatcher/test_message.py
#
from message import addresses, content, destination


#
#   test[s]
#
def test_addresses_text():

    # assert
    assert addresses('a@example.com') == ['a@example.com']


def test_addresses_list():

    # assert
    assert addresses(['a@example.com', 'b@example.com']) == ['a@example.com', 'b@example.com']


def test_addresses_empty():

    # assert
    assert addresses(None) == []


def test_destination_to_only():

    # assert
    assert destination('a@example.com', [], []) == {'ToAddresses': ['a@example.com']}


def test_destination_with_cc_and_bcc():

    # assert
    assert destination('a@example.com', ['c@example.com'], ['b@example.com']) == {
        'ToAddresses'  : ['a@example.com'],
        'CcAddresses'  : ['c@example.com'],
        'BccAddresses' : ['b@example.com']
    }


def test_destination_cc_text():

    # assert
    assert destination('a@example.com', 'c@example.com', None)['CcAddresses'] == ['c@example.com']


def test_content_subject_and_html():

    # item
    item = content('daily', '<p>hi</p>')

    # simple
    simple = item['Simple']

    # assert
    assert simple['Subject'] == {'Data': 'daily'}
    assert simple['Body'] == {'Html': {'Data': '<p>hi</p>'}}
