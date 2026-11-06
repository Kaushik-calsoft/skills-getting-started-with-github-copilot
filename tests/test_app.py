import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def test_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 4,
            "participants": ["existing@mergington.edu"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Wednesdays",
            "max_participants": 3,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(test_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, test_activities):
    # Arrange
    expected_activities = test_activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, test_activities):
    # Arrange
    activity_name = "Art Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in test_activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, test_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@mergington.edu"
    participants_before = test_activities[activity_name]["participants"][:]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert test_activities[activity_name]["participants"] == participants_before


def test_signup_returns_404_for_unknown_activity(client, test_activities):
    # Arrange
    activity_name = "Unknown Club"
    email = "new@mergington.edu"
    participants_before = {
        name: activity["participants"][:]
        for name, activity in test_activities.items()
    }

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert {
        name: activity["participants"]
        for name, activity in test_activities.items()
    } == participants_before


def test_remove_participant_removes_email(client, test_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in test_activities[activity_name]["participants"]


def test_remove_participant_returns_404_for_unknown_activity(client, test_activities):
    # Arrange
    activity_name = "Unknown Club"
    email = "existing@mergington.edu"
    participants_before = {
        name: activity["participants"][:]
        for name, activity in test_activities.items()
    }

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert {
        name: activity["participants"]
        for name, activity in test_activities.items()
    } == participants_before


def test_remove_participant_returns_404_for_unregistered_email(client, test_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "missing@mergington.edu"
    participants_before = test_activities[activity_name]["participants"][:]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert test_activities[activity_name]["participants"] == participants_before