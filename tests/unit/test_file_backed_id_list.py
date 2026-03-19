from __future__ import annotations

from rpg_subreddit_processor.helpers.file_backed_id_list import FileBackedIDList


def test_add_and_exists(tmp_path):
    f = FileBackedIDList(tmp_path / "ids.txt")
    f.add(1)
    f.add(2)
    assert f.exists(1)
    assert f.exists(2)
    assert not f.exists(3)
    f.close()


def test_file_contents(tmp_path):
    path = tmp_path / "ids.txt"
    f = FileBackedIDList(path)
    f.add(10)
    f.add(20)
    f.close()
    assert path.read_text() == "10\n20\n"


def test_reload_from_disk(tmp_path):
    path = tmp_path / "ids.txt"
    f = FileBackedIDList(path)
    f.add(1)
    f.add(2)
    f.close()

    f2 = FileBackedIDList(path)
    assert f2.exists(1)
    assert f2.exists(2)
    assert not f2.exists(3)
    f2.close()


def test_reload_appends_new_ids(tmp_path):
    path = tmp_path / "ids.txt"
    f = FileBackedIDList(path)
    f.add(1)
    f.close()

    f2 = FileBackedIDList(path)
    f2.add(2)
    f2.close()

    assert path.read_text() == "1\n2\n"


def test_empty_file(tmp_path):
    path = tmp_path / "ids.txt"
    path.write_text("")
    f = FileBackedIDList(path)
    assert not f.exists(0)
    f.close()


def test_nonexistent_file(tmp_path):
    f = FileBackedIDList(tmp_path / "new.txt")
    assert not f.exists(99)
    f.close()
