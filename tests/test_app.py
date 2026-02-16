"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestGetActivities:
    """Test cases for retrieving activities"""
    
    def test_get_activities_returns_200(self):
        """Test that /activities endpoint returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that /activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_fields(self):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_contains_chess_club(self):
        """Test that Chess Club is in activities"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignupForActivity:
    """Test cases for signing up for activities"""
    
    def test_signup_new_participant(self):
        """Test signing up a new participant for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "message" in response.json()
        assert "newstudent@mergington.edu" in response.json()["message"]
    
    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self):
        """Test that duplicate signups are rejected"""
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_different_participants(self):
        """Test signing up multiple different participants"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in activity
        activities = client.get("/activities").json()
        assert email1 in activities["Programming Class"]["participants"]
        assert email2 in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Test cases for unregistering from activities"""
    
    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        # First sign up
        email = "unregister_test@mergington.edu"
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Tennis Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify removal
        activities = client.get("/activities").json()
        assert email not in activities["Tennis Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_participant_not_signed_up(self):
        """Test unregistering a participant who is not signed up"""
        response = client.post(
            "/activities/Drama Club/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_and_resign_up(self):
        """Test that a participant can unregister and sign up again"""
        email = "resign_test@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify re-signup worked
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]


class TestRootRedirect:
    """Test cases for root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
