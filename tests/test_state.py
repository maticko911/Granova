from granova import state


def test_save_load_delete_job(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "JOBS_DIR", tmp_path / "jobs")

    path = state.save_job("transkript šžč", "Sestanek", raw_notes="opomba")
    assert path.exists()

    jobs = state.load_jobs()
    assert len(jobs) == 1
    loaded_path, job = jobs[0]
    assert loaded_path == path
    assert job == {"transcript": "transkript šžč", "title": "Sestanek", "raw_notes": "opomba"}

    state.delete_job(path)
    assert not path.exists()
    assert state.load_jobs() == []


def test_corrupt_job_skipped(tmp_path, monkeypatch):
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    (jobs_dir / "bad.json").write_text("{ni json", encoding="utf-8")
    monkeypatch.setattr(state, "JOBS_DIR", jobs_dir)

    assert state.load_jobs() == []


def test_load_jobs_without_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "JOBS_DIR", tmp_path / "neobstaja")
    assert state.load_jobs() == []
