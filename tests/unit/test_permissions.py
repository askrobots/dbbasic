#!/usr/bin/env python3
"""Test ownership-based permissions system"""

import asyncio
import aiohttp
import json
import sys

BASE_URL = "http://localhost:8005"

async def test_public_read():
    """Test that public read permission works without authentication"""
    print("\n🧪 Testing public read (no auth required)...")

    async with aiohttp.ClientSession() as session:
        # Try to read customers without auth (should work - read is public)
        async with session.get(f"{BASE_URL}/api/customers") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Public read successful: {data['total']} records")
            else:
                print(f"❌ Public read failed: {resp.status}")

async def test_authenticated_create():
    """Test that create requires authentication"""
    print("\n🧪 Testing create permission (requires authentication)...")

    async with aiohttp.ClientSession() as session:
        # Try to create without auth (should fail)
        test_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "555-1234",
            "credit_limit": 1000,
            "status": "active"
        }

        async with session.post(f"{BASE_URL}/api/customers", json=test_data) as resp:
            if resp.status == 403:
                print("✅ Create without auth correctly denied")
            else:
                print(f"❌ Unexpected response: {resp.status}")

        # Try to create with auth (should work)
        headers = {"X-User": "user123"}
        async with session.post(f"{BASE_URL}/api/customers", json=test_data, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Create with auth successful: ID {result['id']}")
                return result['id']
            else:
                print(f"❌ Create with auth failed: {resp.status}")
                return None

async def test_owner_update(record_id: int):
    """Test that owner can update their own record"""
    print("\n🧪 Testing owner update permission...")

    if not record_id:
        print("⚠️ Skipping - no record ID")
        return

    async with aiohttp.ClientSession() as session:
        # Try to update as different user (should fail)
        headers = {"X-User": "otheruser"}
        update_data = {"name": "Updated by Other"}

        async with session.put(f"{BASE_URL}/api/customers/{record_id}", json=update_data, headers=headers) as resp:
            if resp.status == 403:
                print("✅ Update by non-owner correctly denied")
            else:
                print(f"❌ Unexpected response: {resp.status}")

        # Try to update as owner (should work)
        headers = {"X-User": "user123"}
        update_data = {"name": "Updated by Owner"}

        async with session.put(f"{BASE_URL}/api/customers/{record_id}", json=update_data, headers=headers) as resp:
            if resp.status == 200:
                print("✅ Update by owner successful")
            else:
                print(f"❌ Update by owner failed: {resp.status}")

        # Try to update as admin (should work)
        headers = {"X-User": "admin"}
        update_data = {"name": "Updated by Admin"}

        async with session.put(f"{BASE_URL}/api/customers/{record_id}", json=update_data, headers=headers) as resp:
            if resp.status == 200:
                print("✅ Update by admin successful")
            else:
                print(f"❌ Update by admin failed: {resp.status}")

async def test_admin_delete(record_id: int):
    """Test that only admin can delete"""
    print("\n🧪 Testing admin-only delete permission...")

    if not record_id:
        print("⚠️ Skipping - no record ID")
        return

    async with aiohttp.ClientSession() as session:
        # Create another test record as a different user
        headers = {"X-User": "user456"}
        test_data = {
            "name": "Delete Test User",
            "email": "delete@example.com",
            "phone": "555-9999",
            "credit_limit": 500,
            "status": "active"
        }

        async with session.post(f"{BASE_URL}/api/customers", json=test_data, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                delete_id = result['id']
                print(f"✅ Created test record: ID {delete_id}")
            else:
                print(f"❌ Failed to create test record: {resp.status}")
                return

        # Try to delete as owner (should fail - delete is admin only)
        headers = {"X-User": "user456"}
        async with session.delete(f"{BASE_URL}/api/customers/{delete_id}", headers=headers) as resp:
            if resp.status == 403:
                print("✅ Delete by owner correctly denied (admin-only)")
            else:
                print(f"❌ Unexpected response: {resp.status}")

        # Try to delete as different user (should fail)
        headers = {"X-User": "otheruser"}
        async with session.delete(f"{BASE_URL}/api/customers/{delete_id}", headers=headers) as resp:
            if resp.status == 403:
                print("✅ Delete by non-admin correctly denied")
            else:
                print(f"❌ Unexpected response: {resp.status}")

        # Try to delete as admin (should work)
        headers = {"X-User": "admin"}
        async with session.delete(f"{BASE_URL}/api/customers/{delete_id}", headers=headers) as resp:
            if resp.status == 200:
                print("✅ Delete by admin successful")
            else:
                print(f"❌ Delete by admin failed: {resp.status}")

async def test_ownership_tracking():
    """Test that ownership fields are properly populated"""
    print("\n🧪 Testing ownership tracking fields...")

    async with aiohttp.ClientSession() as session:
        # Create record as user123
        headers = {"X-User": "user123"}
        test_data = {
            "name": "Ownership Test",
            "email": "ownership@example.com",
            "phone": "555-7777",
            "credit_limit": 2000,
            "status": "active"
        }

        async with session.post(f"{BASE_URL}/api/customers", json=test_data, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                record_id = result['id']

                # Check if created_by field was set
                if result.get('created_by') == 'user123':
                    print(f"✅ created_by field correctly set to 'user123'")
                else:
                    print(f"❌ created_by field incorrect: {result.get('created_by')}")

                # Update the record as admin
                headers = {"X-User": "admin"}
                update_data = {"status": "inactive"}

                async with session.put(f"{BASE_URL}/api/customers/{record_id}", json=update_data, headers=headers) as resp2:
                    if resp2.status == 200:
                        updated = await resp2.json()

                        # Check if updated_by field was set
                        if updated.get('updated_by') == 'admin':
                            print(f"✅ updated_by field correctly set to 'admin'")
                        else:
                            print(f"❌ updated_by field incorrect: {updated.get('updated_by')}")

                        # Verify created_by didn't change
                        if updated.get('created_by') == 'user123':
                            print(f"✅ created_by field preserved as 'user123'")
                        else:
                            print(f"❌ created_by field changed: {updated.get('created_by')}")
            else:
                print(f"❌ Failed to create test record: {resp.status}")

async def main():
    """Run all permission tests"""
    print("=" * 60)
    print("🚀 Testing Ownership-Based Permissions System")
    print("=" * 60)

    try:
        # Test public read
        await test_public_read()

        # Test authenticated create and get record ID
        record_id = await test_authenticated_create()

        # Test owner update permissions
        await test_owner_update(record_id)

        # Test admin-only delete
        await test_admin_delete(record_id)

        # Test ownership field tracking
        await test_ownership_tracking()

        print("\n" + "=" * 60)
        print("✅ All permission tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())