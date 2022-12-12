from bettersafethansorry.utilities import split_user_host, split_user_password_host


def test_split_user_host():
    assert split_user_host('user@host') == ('user', 'host')
    assert split_user_host('user@') == ('user', None)
    assert split_user_host('@host') == (None, 'host')
    assert split_user_host('host') == (None, 'host')
