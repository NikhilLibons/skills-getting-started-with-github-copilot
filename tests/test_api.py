"""Backend API tests for Mergington High School Activities API."""

import pytest


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Verify we get a dict of activities
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify each activity has required fields
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_has_sample_data(self, client, reset_activities):
        """Test that activities include expected sample activities."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify some expected activities exist
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities, f"Expected activity '{activity}' not found"


class TestRootEndpoint:
    """Tests for GET / endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"
    
    def test_root_redirect_follow(self, client):
        """Test following redirect from root endpoint."""
        # Note: TestClient will return 404 for /static since it's not mounted for testing
        # But we can verify the redirect behavior is correct
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        email = "newemail@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for a non-existent activity returns 404."""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test signup with email already registered returns 400."""
        activity = "Chess Club"
        # Use an email that's already in Chess Club from the fixtures
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already" in data["detail"].lower()
    
    @pytest.mark.parametrize("email", [
        "alice@mergington.edu",
        "bob@mergington.edu",
        "charlie@mergington.edu",
    ])
    def test_signup_multiple_participants(self, client, reset_activities, email):
        """Test multiple participants can sign up for the same activity."""
        activity = "Programming Class"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister removes participant from activity."""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Verify participant is there initially
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity returns 404."""
        response = client.delete(
            "/activities/NonexistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_unregister_participant_not_found(self, client, reset_activities):
        """Test unregister of participant not in activity returns 404."""
        activity = "Chess Club"
        email = "notinareneered@mergington.edu"  # Not in Chess Club
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.parametrize("activity", [
        "Chess Club",
        "Programming Class",
        "Gym Class",
    ])
    def test_unregister_from_different_activities(self, client, reset_activities, activity):
        """Test unregistering from different activities works correctly."""
        # First, sign up for the activity
        email = "testuser@mergington.edu"
        
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]


class TestIntegration:
    """Integration tests for multi-step workflows."""
    
    def test_full_signup_and_unregister_flow(self, client, reset_activities):
        """Test complete flow: signup, verify, unregister, verify."""
        activity = "Programming Class"
        email = "integration@mergington.edu"
        
        # Step 1: Verify participant not already registered
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        initial_count = len(activities[activity]["participants"])
        
        # Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Step 3: Verify signup worked
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count + 1
        
        # Step 4: Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Step 5: Verify unregister worked
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count
    
    def test_multiple_signups_and_activities(self, client, reset_activities):
        """Test signing up multiple users for multiple activities."""
        users = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        activities_to_join = ["Chess Club", "Programming Class"]
        
        # Sign up all users for all activities
        for user in users:
            for activity in activities_to_join:
                response = client.post(
                    f"/activities/{activity}/signup",
                    params={"email": user}
                )
                assert response.status_code == 200
        
        # Verify all signups
        response = client.get("/activities")
        activities = response.json()
        for activity in activities_to_join:
            for user in users:
                assert user in activities[activity]["participants"]
