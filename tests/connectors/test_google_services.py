# ruff: noqa: I001
"""Tests for Google Cloud services discovery operations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("google.oauth2.service_account")
pytest.importorskip("googleapiclient")

from extended_data.connectors.google import GoogleConnectorFull


@pytest.fixture
def google_connector():
    """Create Google connector with mocked services."""
    service_account = {
        "type": "service_account",
        "client_email": "test@example.iam.gserviceaccount.com",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
        "private_key_id": "key123",
        "project_id": "test-project",
    }
    with patch("googleapiclient.discovery.build"):
        connector = GoogleConnectorFull(service_account_info=service_account)
        connector.logger = MagicMock()
        return connector


class TestComputeEngine:
    """Tests for Compute Engine operations."""

    def test_list_compute_instances_all_zones(self, google_connector):
        """Test listing compute instances across all zones."""
        mock_service = MagicMock()
        mock_instances = mock_service.instances.return_value
        mock_instances.aggregatedList.return_value.execute.return_value = {
            "items": {
                "zones/us-central1-a": {
                    "instances": [
                        {"name": "instance-1", "zone": "us-central1-a"},
                        {"name": "instance-2", "zone": "us-central1-a"},
                    ]
                },
                "zones/us-east1-b": {"instances": [{"name": "instance-3", "zone": "us-east1-b"}]},
            }
        }
        google_connector.get_compute_service = MagicMock(return_value=mock_service)

        result = google_connector.list_compute_instances("test-project")

        assert len(result) == 3
        assert result[0]["name"] == "instance-1"
        assert result[2]["name"] == "instance-3"

    def test_list_compute_instances_specific_zone(self, google_connector):
        """Test listing compute instances in specific zone."""
        mock_service = MagicMock()
        mock_instances = mock_service.instances.return_value
        mock_instances.list.return_value.execute.return_value = {
            "items": [
                {"name": "instance-1", "zone": "us-central1-a"},
                {"name": "instance-2", "zone": "us-central1-a"},
            ]
        }
        google_connector.get_compute_service = MagicMock(return_value=mock_service)

        result = google_connector.list_compute_instances("test-project", zone="us-central1-a")

        assert len(result) == 2
        mock_instances.list.assert_called_once()

    def test_list_compute_instances_pagination(self, google_connector):
        """Test listing compute instances with pagination."""
        mock_service = MagicMock()
        mock_instances = mock_service.instances.return_value
        mock_instances.aggregatedList.return_value.execute.side_effect = [
            {
                "items": {"zones/us-central1-a": {"instances": [{"name": "instance-1"}]}},
                "nextPageToken": "token123",
            },
            {
                "items": {"zones/us-east1-b": {"instances": [{"name": "instance-2"}]}},
            },
        ]
        google_connector.get_compute_service = MagicMock(return_value=mock_service)

        result = google_connector.list_compute_instances("test-project")

        assert len(result) == 2
        assert mock_instances.aggregatedList.return_value.execute.call_count == 2


class TestGKE:
    """Tests for Google Kubernetes Engine operations."""

    def test_list_gke_clusters(self, google_connector):
        """Test listing GKE clusters."""
        mock_service = MagicMock()
        mock_clusters = mock_service.projects.return_value.locations.return_value.clusters.return_value
        mock_clusters.list.return_value.execute.return_value = {
            "clusters": [
                {"name": "cluster-1", "location": "us-central1"},
                {"name": "cluster-2", "location": "us-east1"},
            ]
        }
        google_connector.get_container_service = MagicMock(return_value=mock_service)

        result = google_connector.list_gke_clusters("test-project")

        assert len(result) == 2
        assert result[0]["name"] == "cluster-1"

    def test_list_gke_clusters_with_location(self, google_connector):
        """Test listing GKE clusters in specific location."""
        mock_service = MagicMock()
        mock_clusters = mock_service.projects.return_value.locations.return_value.clusters.return_value
        mock_clusters.list.return_value.execute.return_value = {
            "clusters": [{"name": "cluster-1", "location": "us-central1"}]
        }
        google_connector.get_container_service = MagicMock(return_value=mock_service)

        result = google_connector.list_gke_clusters("test-project", location="us-central1")

        assert len(result) == 1
        mock_clusters.list.assert_called_once_with(parent="projects/test-project/locations/us-central1")

    def test_get_gke_cluster(self, google_connector):
        """Test getting a specific GKE cluster."""
        mock_service = MagicMock()
        mock_clusters = mock_service.projects.return_value.locations.return_value.clusters.return_value
        mock_clusters.get.return_value.execute.return_value = {
            "name": "cluster-1",
            "location": "us-central1",
            "status": "RUNNING",
        }
        google_connector.get_container_service = MagicMock(return_value=mock_service)

        result = google_connector.get_gke_cluster("test-project", "us-central1", "cluster-1")

        assert result["name"] == "cluster-1"
        assert result["status"] == "RUNNING"

    def test_get_gke_cluster_not_found(self, google_connector):
        """Test getting non-existent GKE cluster."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_clusters = mock_service.projects.return_value.locations.return_value.clusters.return_value
        mock_resp = MagicMock()
        mock_resp.status = 404
        error = HttpError(mock_resp, b"Not found")
        mock_clusters.get.return_value.execute.side_effect = error
        google_connector.get_container_service = MagicMock(return_value=mock_service)

        result = google_connector.get_gke_cluster("test-project", "us-central1", "missing-cluster")

        assert result is None


class TestCloudStorage:
    """Tests for Cloud Storage operations."""

    def test_list_storage_buckets(self, google_connector):
        """Test listing Cloud Storage buckets."""
        mock_service = MagicMock()
        mock_buckets = mock_service.buckets.return_value
        mock_buckets.list.return_value.execute.return_value = {
            "items": [
                {"name": "bucket-1", "location": "US"},
                {"name": "bucket-2", "location": "EU"},
            ]
        }
        google_connector.get_storage_service = MagicMock(return_value=mock_service)

        result = google_connector.list_storage_buckets("test-project")

        assert len(result) == 2
        assert result[0]["name"] == "bucket-1"


class TestCloudSQL:
    """Tests for Cloud SQL operations."""

    def test_list_sql_instances(self, google_connector):
        """Test listing Cloud SQL instances."""
        mock_service = MagicMock()
        mock_instances = mock_service.instances.return_value
        mock_instances.list.return_value.execute.return_value = {
            "items": [
                {"name": "instance-1", "databaseVersion": "MYSQL_8_0"},
                {"name": "instance-2", "databaseVersion": "POSTGRES_13"},
            ]
        }
        google_connector.get_sqladmin_service = MagicMock(return_value=mock_service)

        result = google_connector.list_sql_instances("test-project")

        assert len(result) == 2
        assert result[0]["databaseVersion"] == "MYSQL_8_0"


class TestPubSub:
    """Tests for Pub/Sub operations."""

    def test_list_pubsub_topics(self, google_connector):
        """Test listing Pub/Sub topics."""
        mock_service = MagicMock()
        mock_topics = mock_service.projects.return_value.topics.return_value
        mock_topics.list.return_value.execute.return_value = {
            "topics": [
                {"name": "projects/test-project/topics/topic-1"},
                {"name": "projects/test-project/topics/topic-2"},
            ]
        }
        google_connector.get_pubsub_service = MagicMock(return_value=mock_service)

        result = google_connector.list_pubsub_topics("test-project")

        assert len(result) == 2
        assert "topic-1" in result[0]["name"]

    def test_list_pubsub_subscriptions(self, google_connector):
        """Test listing Pub/Sub subscriptions."""
        mock_service = MagicMock()
        mock_subs = mock_service.projects.return_value.subscriptions.return_value
        mock_subs.list.return_value.execute.return_value = {
            "subscriptions": [
                {"name": "projects/test-project/subscriptions/sub-1"},
                {"name": "projects/test-project/subscriptions/sub-2"},
            ]
        }
        google_connector.get_pubsub_service = MagicMock(return_value=mock_service)

        result = google_connector.list_pubsub_subscriptions("test-project")

        assert len(result) == 2
        assert "sub-1" in result[0]["name"]


class TestCloudKMS:
    """Tests for Cloud KMS operations."""

    def test_list_kms_keyrings(self, google_connector):
        """Test listing KMS keyrings."""
        mock_service = MagicMock()
        mock_keyrings = mock_service.projects.return_value.locations.return_value.keyRings.return_value
        mock_keyrings.list.return_value.execute.return_value = {
            "keyRings": [
                {"name": "projects/test-project/locations/us/keyRings/keyring-1"},
                {"name": "projects/test-project/locations/us/keyRings/keyring-2"},
            ]
        }
        google_connector.get_cloudkms_service = MagicMock(return_value=mock_service)

        result = google_connector.list_kms_keyrings("test-project", "us")

        assert len(result) == 2
        assert "keyring-1" in result[0]["name"]

    def test_create_kms_keyring(self, google_connector):
        """Test creating a KMS keyring."""
        mock_service = MagicMock()
        mock_keyrings = mock_service.projects.return_value.locations.return_value.keyRings.return_value
        mock_keyrings.create.return_value.execute.return_value = {
            "name": "projects/test-project/locations/us/keyRings/new-keyring"
        }
        google_connector.get_cloudkms_service = MagicMock(return_value=mock_service)

        result = google_connector.create_kms_keyring("test-project", "us", "new-keyring")

        assert "new-keyring" in result["name"]

    def test_create_kms_key(self, google_connector):
        """Test creating a crypto key."""
        mock_service = MagicMock()
        mock_projects = mock_service.projects.return_value
        mock_locations = mock_projects.locations.return_value
        mock_keyrings = mock_locations.keyRings.return_value
        mock_keys = mock_keyrings.cryptoKeys.return_value
        mock_keys.create.return_value.execute.return_value = {
            "name": "projects/test-project/locations/us/keyRings/kr1/cryptoKeys/new-key"
        }
        google_connector.get_cloudkms_service = MagicMock(return_value=mock_service)

        result = google_connector.create_kms_key("test-project", "us", "kr1", "new-key")

        assert "new-key" in result["name"]
