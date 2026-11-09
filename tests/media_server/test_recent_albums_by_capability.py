"""The incremental scan reads recently added albums through the declared
contract, so a server with no branch of its own in the update worker
(Music Assistant) still gets an incremental scan instead of an empty one."""

from core.database_update_worker import DatabaseUpdateWorker
from core.media_server.base import MediaServerBase
from core.media_server.contract import Capability


class _Declares(MediaServerBase):
    """A client that declares RECENTLY_ADDED and records the call."""
    CAPABILITIES = frozenset({Capability.RECENTLY_ADDED})

    def __init__(self, albums):
        """Hold the albums to return and count the calls."""
        self.albums = albums
        self.calls = []

    def get_recently_added_albums(self, limit=400):
        """Return the canned albums, recording the limit asked for."""
        self.calls.append(limit)
        return self.albums


class _Silent(MediaServerBase):
    """A client that declares nothing."""

    def get_recently_added_albums(self, limit=400):
        """Fail the test if the worker calls an undeclared method."""
        raise AssertionError("an undeclared capability must not be called")


def _worker(client, server_type, tmp_path):
    """A worker over a throwaway database, as the web scan builds one."""
    return DatabaseUpdateWorker(media_client=client, database_path=str(tmp_path / "m.db"),
                                server_type=server_type, force_sequential=True)


def test_music_assistant_recent_albums_come_from_the_contract(tmp_path):
    client = _Declares(["a1", "a2"])
    w = _worker(client, "music_assistant", tmp_path)
    assert w._get_recent_albums_for_server() == ["a1", "a2"]
    assert client.calls == [400]


def test_a_server_that_declares_nothing_still_gets_an_empty_list(tmp_path):
    w = _worker(_Silent(), "music_assistant", tmp_path)
    assert w._get_recent_albums_for_server() == []


def test_none_from_the_client_is_an_empty_list(tmp_path):
    w = _worker(_Declares(None), "music_assistant", tmp_path)
    assert w._get_recent_albums_for_server() == []
