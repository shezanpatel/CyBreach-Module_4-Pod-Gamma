from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import PlayerEntry

client = TestClient(app)

def test_get_global_leaderboard_success():
    mock_entries = [PlayerEntry(rank=1, username="alice", score=100.0)]
    with patch("app.api.leaderboard.get_leaderboard_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_top_players.return_value = (mock_entries, 1)
        mock_get_svc.return_value = mock_svc
        res = client.get(f"/leaderboard/global?view=absolute&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert data["dimension"] == "global"
        assert data["total_players"] == 1
        assert data["limit"] == 5
        assert data["entries"][0]["username"] == "alice"

def test_get_leaderboard_invalid_dimension():
    res = client.get("/leaderboard/invalid_dim")
    assert res.status_code == 400
