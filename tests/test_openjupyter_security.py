"""Tests for the secured /openJupyter/ and /stopJupyter/ endpoints."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a test API key before importing the app module
TEST_API_KEY = "test-secret-key-12345"


@pytest.fixture(autouse=True)
def reset_jupyter_process():
    """Reset the module-level jupyter_process before each test."""
    import fri.server.main as mod
    mod.jupyter_process = None
    yield
    mod.jupyter_process = None


@pytest.fixture
def client():
    """Create a Flask test client with the API key configured."""
    with patch.dict(os.environ, {"CONCORE_API_KEY": TEST_API_KEY}):
        # Re-read env var after patching
        import fri.server.main as mod
        mod.API_KEY = TEST_API_KEY
        mod.app.config["TESTING"] = True
        with mod.app.test_client() as c:
            yield c


@pytest.fixture
def client_no_key():
    """Create a Flask test client without API key configured."""
    import fri.server.main as mod
    mod.API_KEY = None
    mod.app.config["TESTING"] = True
    with mod.app.test_client() as c:
        yield c


class TestOpenJupyterAuth:
    """Test authentication on /openJupyter/ endpoint."""

    def test_missing_api_key_header_returns_403(self, client):
        """Request without X-API-KEY header should be rejected."""
        resp = client.post("/openJupyter/")
        assert resp.status_code == 403

    def test_wrong_api_key_returns_403(self, client):
        """Request with wrong key should be rejected."""
        resp = client.post("/openJupyter/", headers={"X-API-KEY": "wrong-key"})
        assert resp.status_code == 403

    def test_server_without_api_key_configured_returns_500(self, client_no_key):
        """If CONCORE_API_KEY is not set on server, return 500."""
        resp = client_no_key.post(
            "/openJupyter/", headers={"X-API-KEY": "anything"}
        )
        assert resp.status_code == 500


class TestOpenJupyterProcess:
    """Test process control on /openJupyter/ endpoint."""

    @patch("fri.server.main.subprocess.Popen")
    def test_authorized_request_starts_jupyter(self, mock_popen, client):
        """Valid API key should start Jupyter Lab."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # process running
        mock_popen.return_value = mock_proc

        resp = client.post(
            "/openJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Jupyter Lab started"

        # Verify Popen was called with --no-browser and DEVNULL
        call_args = mock_popen.call_args
        assert "--no-browser" in call_args[0][0]
        assert call_args[1].get("shell") is False

    @patch("fri.server.main.subprocess.Popen")
    def test_duplicate_launch_returns_409(self, mock_popen, client):
        """Second launch while first is still running should return 409."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        mock_popen.return_value = mock_proc

        # First launch
        resp1 = client.post(
            "/openJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp1.status_code == 200

        # Second launch should be rejected
        resp2 = client.post(
            "/openJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp2.status_code == 409
        data = resp2.get_json()
        assert data["message"] == "Jupyter already running"

    @patch("fri.server.main.subprocess.Popen", side_effect=Exception("fail"))
    def test_popen_failure_returns_500(self, mock_popen, client):
        """If Popen raises, return 500."""
        resp = client.post(
            "/openJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data


class TestStopJupyter:
    """Test /stopJupyter/ endpoint."""

    def test_stop_without_auth_returns_403(self, client):
        """Request without API key should be rejected."""
        resp = client.post("/stopJupyter/")
        assert resp.status_code == 403

    def test_stop_when_no_process_returns_404(self, client):
        """Stop with no running process returns 404."""
        resp = client.post(
            "/stopJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp.status_code == 404

    @patch("fri.server.main.subprocess.Popen")
    def test_stop_running_process_returns_200(self, mock_popen, client):
        """Stop a running Jupyter instance returns 200."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # running
        mock_popen.return_value = mock_proc

        # Start first
        client.post("/openJupyter/", headers={"X-API-KEY": TEST_API_KEY})

        # Stop
        resp = client.post(
            "/stopJupyter/", headers={"X-API-KEY": TEST_API_KEY}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "Jupyter stopped"
        mock_proc.terminate.assert_called_once()
