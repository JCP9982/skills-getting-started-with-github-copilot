from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)

    yield

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    activity = response.json()[expected_activity]
    assert response.status_code == 200
    assert activity["description"]
    assert activity["schedule"]
    assert activity["max_participants"] == 12
    assert "michael@mergington.edu" in activity["participants"]


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Soccer Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity_name]["participants"]
    assert response.json()["message"] == (
        f"Signed up {email} for {activity_name}"
    )


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_delete_removes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]
    assert response.json()["message"] == (
        f"Unregistered {email} from {activity_name}"
    )


def test_delete_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_unregistered_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"