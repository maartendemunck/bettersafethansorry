from bettersafethansorry.utilities import split_user_host, split_user_password_host


def test_split_user_host():
    assert split_user_host('user@host') == ('user', 'host')
    assert split_user_host('user@') == ('user', None)
    assert split_user_host('@host') == (None, 'host')
    assert split_user_host('host') == (None, 'host')


def test_split_user_password_host():
    assert split_user_password_host(
        'user:password@host.domain') == ('user', 'password', 'host.domain')
    assert split_user_password_host(
        'user:@host.domain') == ('user', '', 'host.domain')
    assert split_user_password_host(
        'user@host.domain') == ('user', None, 'host.domain')
    assert split_user_password_host(
        'user:password@') == ('user', 'password', None)
    assert split_user_password_host('user:@') == ('user', '', None)
    assert split_user_password_host('user@') == ('user', None, None)
    assert split_user_password_host(
        '@host.domain') == (None, None, 'host.domain')
    assert split_user_password_host(
        'host.domain') == (None, None, 'host.domain')
