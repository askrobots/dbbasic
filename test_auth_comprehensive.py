#!/usr/bin/env python3
"""
Comprehensive auth service testing
Tests all auth operations including user management and access control
"""

import requests
import json
import time

BASE_URL = "http://localhost:8010"

def test_health():
    """Test service health"""
    print("Testing service health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["port"] == 8010
    print("✅ Health check passed")

def test_register():
    """Test user registration"""
    print("\nTesting registration...")

    # Register user1
    user1 = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "alice123"
    }
    r = requests.post(f"{BASE_URL}/api/register", json=user1)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    print("✅ User 'alice' registered")

    # Register user2
    user2 = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "bob456"
    }
    r = requests.post(f"{BASE_URL}/api/register", json=user2)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    print("✅ User 'bob' registered")

    # Try duplicate username
    dup = {
        "username": "alice",
        "email": "alice2@example.com",
        "password": "test"
    }
    r = requests.post(f"{BASE_URL}/api/register", json=dup)
    data = r.json()
    assert data["success"] == False
    print("✅ Duplicate username rejected")

def test_login():
    """Test user login"""
    print("\nTesting login...")

    # Login as alice
    creds = {
        "username": "alice",
        "password": "alice123"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=creds)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    assert "token" in data
    alice_token = data["token"]
    print(f"✅ Alice logged in, token: {alice_token[:20]}...")

    # Login as bob
    creds = {
        "username": "bob",
        "password": "bob456"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=creds)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    assert "token" in data
    bob_token = data["token"]
    print(f"✅ Bob logged in, token: {bob_token[:20]}...")

    # Wrong password
    bad_creds = {
        "username": "alice",
        "password": "wrong"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=bad_creds)
    data = r.json()
    assert data["success"] == False
    print("✅ Wrong password rejected")

    # Login with email
    email_creds = {
        "username": "alice@example.com",
        "password": "alice123"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=email_creds)
    data = r.json()
    assert data["success"] == True
    print("✅ Login with email works")

    return alice_token, bob_token

def test_verify_token(alice_token, bob_token):
    """Test token verification"""
    print("\nTesting token verification...")

    # Verify alice token
    headers = {"Authorization": f"Bearer {alice_token}"}
    r = requests.get(f"{BASE_URL}/api/verify", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    assert data["user"]["username"] == "alice"
    print("✅ Alice token verified")

    # Verify bob token
    headers = {"Authorization": f"Bearer {bob_token}"}
    r = requests.get(f"{BASE_URL}/api/verify", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    assert data["user"]["username"] == "bob"
    print("✅ Bob token verified")

    # Invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    r = requests.get(f"{BASE_URL}/api/verify", headers=headers)
    data = r.json()
    assert data["success"] == False
    print("✅ Invalid token rejected")

def test_change_password(alice_token):
    """Test password change"""
    print("\nTesting password change...")

    headers = {"Authorization": f"Bearer {alice_token}"}
    payload = {
        "old_password": "alice123",
        "new_password": "newalice456"
    }
    r = requests.post(f"{BASE_URL}/api/change-password", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    print("✅ Password changed")

    # Try login with new password
    creds = {
        "username": "alice",
        "password": "newalice456"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=creds)
    data = r.json()
    assert data["success"] == True
    print("✅ Login with new password works")

    # Old password shouldn't work
    creds = {
        "username": "alice",
        "password": "alice123"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=creds)
    data = r.json()
    assert data["success"] == False
    print("✅ Old password rejected")

def test_logout(bob_token):
    """Test logout"""
    print("\nTesting logout...")

    # Logout
    headers = {"Authorization": f"Bearer {bob_token}"}
    r = requests.post(f"{BASE_URL}/api/logout", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    print("✅ Bob logged out")

    # Token should be invalid now
    r = requests.get(f"{BASE_URL}/api/verify", headers=headers)
    data = r.json()
    assert data["success"] == False
    print("✅ Token invalidated after logout")

def test_admin_login():
    """Test admin account"""
    print("\nTesting admin account...")

    creds = {
        "username": "admin",
        "password": "admin123"
    }
    r = requests.post(f"{BASE_URL}/api/login", json=creds)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] == True
    assert data["user"]["is_admin"] == True
    print("✅ Admin login works")
    return data["token"]

def test_access_control_simulation():
    """Simulate access control between users"""
    print("\nSimulating access control...")

    # This demonstrates how the auth service would be used
    # In a real system, other services would verify tokens

    # Create alice session
    alice_login = requests.post(f"{BASE_URL}/api/login", json={
        "username": "alice@example.com",
        "password": "newalice456"
    })
    alice_token = alice_login.json()["token"]

    # Create bob session
    bob_reg = requests.post(f"{BASE_URL}/api/register", json={
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "charlie789"
    })

    bob_login = requests.post(f"{BASE_URL}/api/login", json={
        "username": "charlie",
        "password": "charlie789"
    })
    charlie_token = bob_login.json()["token"]

    # Verify different users get different tokens
    assert alice_token != charlie_token
    print("✅ Different users get different tokens")

    # Verify token contains user info
    alice_verify = requests.get(f"{BASE_URL}/api/verify",
                                headers={"Authorization": f"Bearer {alice_token}"})
    charlie_verify = requests.get(f"{BASE_URL}/api/verify",
                                  headers={"Authorization": f"Bearer {charlie_token}"})

    alice_user = alice_verify.json()["user"]
    charlie_user = charlie_verify.json()["user"]

    assert alice_user["username"] == "alice"
    assert charlie_user["username"] == "charlie"
    assert alice_user["user_id"] != charlie_user["user_id"]
    print("✅ Tokens correctly identify different users")

def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("COMPREHENSIVE AUTH SERVICE TESTING")
    print("=" * 50)

    test_health()
    test_register()
    alice_token, bob_token = test_login()
    test_verify_token(alice_token, bob_token)
    test_change_password(alice_token)
    test_logout(bob_token)
    admin_token = test_admin_login()
    test_access_control_simulation()

    print("\n" + "=" * 50)
    print("✅ ALL AUTH TESTS PASSED!")
    print("=" * 50)
    print("\nAuth service features verified:")
    print("- User registration with duplicate prevention")
    print("- Login with username or email")
    print("- JWT token generation and verification")
    print("- Password change functionality")
    print("- Session logout and invalidation")
    print("- Admin account access")
    print("- User isolation (different tokens for different users)")
    print("\nThe auth service is ready for integration with other services!")

if __name__ == "__main__":
    # Wait a bit for service to be ready
    time.sleep(2)
    run_all_tests()