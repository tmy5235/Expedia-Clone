from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app import config
from app.main import create_app


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project = tmp_path / "project"
    helper = project / "backend" / "app" / "config.py"
    helper.parent.mkdir(parents=True)
    monkeypatch.setattr(config, "__file__", str(helper))
    # Register restoration even if dotenv adds a previously absent variable.
    monkeypatch.setenv("GEOAPIFY_API_KEY", "")
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    monkeypatch.delenv("PYTHON_DOTENV_DISABLED", raising=False)
    # A competing file in the working directory must never be selected.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / ".env").write_text("GEOAPIFY_API_KEY=fictional-wrong-directory\n")
    monkeypatch.chdir(elsewhere)
    return project / ".env"


@pytest.mark.parametrize("contents,expected", [
    (None, ""),
    ("# Setting absent\n", ""),
    ("GEOAPIFY_API_KEY=\n", ""),
    ('GEOAPIFY_API_KEY="  \\t  "\n', ""),
    ('GEOAPIFY_API_KEY=" fictional-test-key "\n', "fictional-test-key"),
])
def test_config_and_health(
    env_file: Path, tmp_path: Path, contents: str | None, expected: str,
) -> None:
    if contents is not None:
        env_file.write_text(contents)
    assert config.load_geoapify_api_key() == expected
    with TestClient(create_app(tmp_path / "test.sqlite3")) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "geoapify": "key is configured" if expected else "key is not configured",
        }
        assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("value", ["fictional-process-key", "", " \t "])
def test_process_environment_takes_precedence(
    env_file: Path, monkeypatch: pytest.MonkeyPatch, value: str,
) -> None:
    env_file.write_text("GEOAPIFY_API_KEY=fictional-file-key\n")
    monkeypatch.setenv("GEOAPIFY_API_KEY", value)
    assert config.load_geoapify_api_key() == value.strip()


def test_health_configuration_is_a_startup_snapshot(
    env_file: Path, tmp_path: Path,
) -> None:
    env_file.write_text("GEOAPIFY_API_KEY=\n")
    with TestClient(create_app(tmp_path / "test.sqlite3")) as client:
        env_file.write_text("GEOAPIFY_API_KEY=fictional-new-key\n")
        assert client.get("/api/health").json()["geoapify"] == "key is not configured"
