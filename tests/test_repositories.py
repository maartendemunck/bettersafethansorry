import subprocess

from bettersafethansorry.actions.repositories import MirrorGitRepository


class FakeLogger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def git(*args, cwd=None):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)


def make_source(path):
    git('init', '--bare', '-b', 'master', str(path))
    work = path.parent / 'work'
    git('clone', str(path), str(work))
    git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit',
        '--allow-empty', '-m', 'one', cwd=work)
    git('push', 'origin', 'master', cwd=work)
    return work


def refs(path):
    return subprocess.run(['git', '-C', str(path), 'rev-parse', 'master'],
                          check=True, capture_output=True, text=True).stdout


def test_clone_update_and_verify(tmp_path):
    source = tmp_path / 'source.git'
    work = make_source(source)
    destination = tmp_path / 'mirror.git'
    config = {'source-directory': str(source), 'destination-directory': str(destination)}

    assert MirrorGitRepository(dict(config), FakeLogger()).do(False) == []
    assert refs(destination) == refs(source)

    git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit',
        '--allow-empty', '-m', 'two', cwd=work)
    git('push', 'origin', 'master', cwd=work)
    action = MirrorGitRepository(dict(config), FakeLogger())
    assert action.do(False) == []
    assert refs(destination) == refs(source)
    assert action.verify(False) == []


def test_source_host_in_url():
    action = MirrorGitRepository({'source-host': 'u@h', 'source-directory': '/r.git',
                                  'destination-directory': '/nonexistent/m.git'}, FakeLogger())
    assert action._compose_do_command() == ['git', 'clone', '--mirror', 'u@h:/r.git', '/nonexistent/m.git']
