"""Tests for ConnectivityService."""

import time
from unittest.mock import patch, MagicMock

import httpx
from daynimal.connectivity import ConnectivityService


class TestConnectivityService:
    @patch("daynimal.connectivity.httpx.head")
    def test_check_online(self, mock_head):
        svc = ConnectivityService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        assert svc.check() is True
        assert svc.is_online is True

    @patch(
        "daynimal.connectivity.httpx.head", side_effect=httpx.ConnectError("no network")
    )
    def test_check_offline_request_error(self, mock_head):
        svc = ConnectivityService()
        assert svc.check() is False
        assert svc.is_online is False

    @patch(
        "daynimal.connectivity.httpx.head",
        side_effect=httpx.TimeoutException("timeout"),
    )
    def test_check_offline_timeout(self, mock_head):
        svc = ConnectivityService()
        assert svc.check() is False

    @patch("daynimal.connectivity.httpx.head")
    def test_check_server_error(self, mock_head):
        svc = ConnectivityService()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_head.return_value = mock_resp
        assert svc.check() is False

    @patch("daynimal.connectivity.httpx.head")
    def test_cache_ttl_not_expired(self, mock_head):
        svc = ConnectivityService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        svc.check()
        assert mock_head.call_count == 1
        # Access is_online again - should use cache
        _ = svc.is_online
        assert mock_head.call_count == 1

    @patch("daynimal.connectivity.httpx.head")
    def test_cache_ttl_expired(self, mock_head):
        svc = ConnectivityService()
        svc.CACHE_TTL = 0.01  # Very short TTL
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        _ = svc.is_online
        assert mock_head.call_count == 1
        time.sleep(0.02)
        _ = svc.is_online
        assert mock_head.call_count == 2

    def test_set_offline(self):
        svc = ConnectivityService()
        svc.set_online()
        assert svc.is_online is True
        svc.set_offline()
        assert svc._is_online is False

    def test_set_online(self):
        svc = ConnectivityService()
        svc.set_offline()
        svc.set_online()
        assert svc._is_online is True

    def test_force_offline(self):
        svc = ConnectivityService()
        svc.set_online()
        svc.force_offline = True
        assert svc.is_online is False
        # check() should also return False when forced
        assert svc.check() is False

    @patch("daynimal.connectivity.httpx.head")
    def test_force_offline_toggle(self, mock_head):
        svc = ConnectivityService()
        svc.force_offline = True
        assert svc.is_online is False
        svc.force_offline = False
        # After unforcing, should trigger a check
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        assert svc.is_online is True

    @patch("daynimal.connectivity.httpx.head")
    def test_initial_state_triggers_check(self, mock_head):
        svc = ConnectivityService()
        assert svc._is_online is None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        _ = svc.is_online
        assert mock_head.call_count == 1
