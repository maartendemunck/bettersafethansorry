import gzip

import pytest

from bettersafethansorry.actions.archive import ArchiveDconf


class FakeLogger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def make_action(tmp_path, **extra):
    config = {'source-directory': '/org/gnome/', 'destination-file': str(tmp_path / 'dconf.txt'), **extra}
    return ArchiveDconf(config, FakeLogger())


@pytest.mark.parametrize('directory', ['org/gnome/', '/org/gnome', '/org/key'])
def test_source_directory_must_start_and_end_with_slash(tmp_path, directory):
    with pytest.raises(ValueError):
        make_action(tmp_path, **{'source-directory': directory})


def test_archive_command(tmp_path):
    action = make_action(tmp_path, **{'source-host': 'user@host'})
    assert action._compose_archive_commands() == [['ssh', 'user@host', "dconf dump '/org/gnome/'"]]
    assert make_action(tmp_path)._compose_archive_commands() == [['dconf', 'dump', '/org/gnome/']]


def test_verify_fails_on_empty_dump(tmp_path):
    action = make_action(tmp_path, compression='gzip -c')
    destination = tmp_path / 'dconf.txt'
    destination.write_bytes(gzip.compress(b''))
    assert action.verify(False) != []
    destination.write_bytes(gzip.compress(b'[/]\nkey=1\n'))
    assert action.verify(False) == []


def test_do_fails_on_empty_dump_and_keeps_old_backup(tmp_path):
    destination = tmp_path / 'dconf.txt.gz'
    config = {'destination-file': str(destination), 'compression': 'gzip -c', 'keep': 1}
    assert ArchiveDconf({'source-directory': '/org/gnome/desktop/interface/', **config}, FakeLogger()).do(False) == []
    good = destination.read_bytes()
    assert ArchiveDconf({'source-directory': '/nonexistent-bsts-test/', **config}, FakeLogger()).do(False) != []
    assert destination.read_bytes() == good
    assert not (tmp_path / 'dconf.txt.gz.tmp').exists()
    assert [p.name for p in tmp_path.iterdir()] == ['dconf.txt.gz']
