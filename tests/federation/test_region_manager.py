"""
OmniWatch 2.0 — Federation
Component: Region Manager Tests
Layer: Enterprise (Phase 6)
Purpose: Unit tests for region registration, health checks, and querying
"""

from unittest.mock import Mock, patch


class TestRegionManager:
    """Test cases for RegionManager class."""

    @patch('federation.region_manager.clickhouse_connect')
    @patch('federation.region_manager.redis')
    def test_register_region(self, mock_redis, mock_ch):
        """Test that register_region inserts region into ClickHouse."""
        mock_client = Mock()
        mock_ch.get_client.return_value = mock_client
        mock_redis_client = Mock()
        mock_redis.Redis.return_value = mock_redis_client

        from federation.region_manager import RegionManager
        manager = RegionManager()

        manager.register_region(
            region_id="us-east-1",
            endpoint="https://us-east-1.omniwatch.io",
            display_name="US East 1",
            metadata='{"cloud_provider": "aws"}'
        )

        mock_client.insert.assert_called_once()
        call_args = mock_client.insert.call_args
        assert call_args[0][0] == "omniwatch.regions"
        assert "us-east-1" in call_args[0][1][0]

    @patch('federation.region_manager.clickhouse_connect')
    @patch('federation.region_manager.redis')
    @patch('federation.region_manager.requests')
    def test_health_check_healthy(self, mock_requests, mock_redis, mock_ch):
        """Test health_check returns healthy status when /health returns 200."""
        mock_client = Mock()
        mock_ch.get_client.return_value = mock_client
        mock_redis_client = Mock()
        mock_redis.Redis.return_value = mock_redis_client

        # Mock the query that fetches the endpoint
        mock_query_result = Mock()
        mock_query_result.result_rows = [["https://us-east-1.omniwatch.io"]]
        mock_client.query.return_value = mock_query_result

        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        from federation.region_manager import RegionManager
        manager = RegionManager()

        result = manager.health_check("us-east-1")

        assert result["status"] == "healthy"
        mock_client.command.assert_called()
        mock_redis_client.setex.assert_called_once()

    @patch('federation.region_manager.clickhouse_connect')
    @patch('federation.region_manager.redis')
    @patch('federation.region_manager.requests')
    def test_health_check_offline(self, mock_requests, mock_redis, mock_ch):
        """Test health_check returns offline status when connection fails."""
        mock_client = Mock()
        mock_ch.get_client.return_value = mock_client
        mock_redis_client = Mock()
        mock_redis.Redis.return_value = mock_redis_client

        # Mock the query that fetches the endpoint
        mock_query_result = Mock()
        mock_query_result.result_rows = [["https://us-east-1.omniwatch.io"]]
        mock_client.query.return_value = mock_query_result

        mock_requests.get.side_effect = Exception("Connection refused")

        from federation.region_manager import RegionManager
        manager = RegionManager()

        result = manager.health_check("us-east-1")

        assert result["status"] == "offline"
        mock_client.command.assert_called()
        mock_redis_client.setex.assert_called_once()

    @patch('federation.region_manager.clickhouse_connect')
    @patch('federation.region_manager.redis')
    def test_get_healthy_regions(self, mock_redis, mock_ch):
        """Test get_healthy_regions returns only healthy regions."""
        mock_client = Mock()
        mock_ch.get_client.return_value = mock_client
        mock_redis_client = Mock()
        mock_redis.Redis.return_value = mock_redis_client

        # Mock query result — simulates what ClickHouse returns after WHERE status='healthy'
        mock_result = Mock()
        mock_result.result_rows = [
            ("us-east-1", "https://us-east-1.io", "US East 1", "healthy"),
            ("ap-south-1", "https://ap-south-1.io", "AP South 1", "healthy"),
        ]
        mock_client.query.return_value = mock_result

        from federation.region_manager import RegionManager
        manager = RegionManager()

        result = manager.get_healthy_regions()

        assert len(result) == 2
        region_ids = [r["region_id"] for r in result]
        assert "us-east-1" in region_ids
        assert "ap-south-1" in region_ids
