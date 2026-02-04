import tempfile
import os
from bhv.storage.git_adapter import GitAdapter


def test_save_and_history():
    with tempfile.TemporaryDirectory() as tmp:
        adapter = GitAdapter(tmp)
        rel = os.path.join('patientA', 'notes.txt')
        commit1 = adapter.save(rel, b'first version', user_id='user1', action='create')
        commit2 = adapter.save(rel, b'second version', user_id='user2', action='edit')

        hist = adapter.history(rel)
        assert len(hist) == 2
        # latest content should be second version
        data = adapter.get(rel)
        assert data == b'second version'

        # retrieve first version by commit hash
        data1 = adapter.get(rel, version=hist[0]['hexsha'])
        assert data1 == b'first version'
