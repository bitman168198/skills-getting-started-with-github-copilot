"""Tests for the FastAPI application."""

import pytest
from urllib.parse import quote


class TestActivities:
    """Tests for the activities endpoints."""

    def test_root_redirect(self, client):
        """Test that root redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200

        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

        # Check structure of an activity
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that expected activities are in the list."""
        response = client.get("/activities")
        activities = response.json()

        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        ]

        for activity in expected_activities:
            assert activity in activities


class TestSignup:
    """Tests for the signup endpoint."""

    def test_signup_for_activity(self, client):
        """Test signing up for an activity."""
        email = "test@mergington.edu"
        activity = "Chess Club"

        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])

        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
        )

        assert response.status_code == 200
        assert "message" in response.json()
        assert email in response.json()["message"]

        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu",
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_with_special_characters_in_email(self, client):
        """Test signing up with email containing special characters."""
        email = "test+special@mergington.edu"
        activity = "Programming Class"

        response = client.post(
            f"/activities/{activity}/signup?email={quote(email)}",
        )

        assert response.status_code == 200

        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestUnregister:
    """Tests for the unregister endpoint."""

    def test_unregister_participant(self, client):
        """Test unregistering a participant from an activity."""
        activity = "Chess Club"

        # Get current participants
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        initial_count = len(participants)

        if initial_count > 0:
            email_to_remove = participants[0]

            # Unregister
            response = client.delete(
                f"/activities/{activity}/unregister?email={email_to_remove}",
            )

            assert response.status_code == 200
            assert "message" in response.json()

            # Verify participant was removed
            response = client.get("/activities")
            new_count = len(response.json()[activity]["participants"])
            assert new_count == initial_count - 1
            assert email_to_remove not in response.json()[activity]["participants"]

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant that doesn't exist."""
        activity = "Tennis Club"
        email = "nonexistent@mergington.edu"

        response = client.delete(
            f"/activities/{activity}/unregister?email={email}",
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu",
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestActivityDetails:
    """Tests for activity details validation."""

    def test_activity_has_required_fields(self, client):
        """Test that all activities have required fields."""
        response = client.get("/activities")
        activities = response.json()

        required_fields = [
            "description",
            "schedule",
            "max_participants",
            "participants",
        ]

        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert (
                    field in activity_data
                ), f"Activity '{activity_name}' missing field '{field}'"

    def test_participants_count_valid(self, client):
        """Test that participant count doesn't exceed max_participants."""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]

            assert (
                participant_count <= max_participants
            ), f"Activity '{activity_name}' has too many participants"

    def test_participants_are_strings(self, client):
        """Test that all participants are strings (emails)."""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(
                    participant, str
                ), f"Participant in '{activity_name}' is not a string"
