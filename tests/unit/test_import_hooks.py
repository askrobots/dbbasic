#!/usr/bin/env python3
"""Test import functionality with hook execution"""

import asyncio
import aiohttp
import csv
import json
import io
import sys
from pathlib import Path

BASE_URL = "http://localhost:8005"

# Global flag to track if hooks were called
hooks_called = []

async def test_csv_import_with_hooks():
    """Test CSV import with hooks enabled"""
    print("\n🧪 Testing CSV import WITH hooks...")

    # Create CSV data
    csv_data = """name,email,phone,credit_limit,status
Test User 1,test1@example.com,555-0001,1000,active
Test User 2,test2@example.com,555-0002,2000,pending
Invalid Email,not-an-email,,3000,active"""

    async with aiohttp.ClientSession() as session:
        # Clear existing data first
        await session.delete(f"{BASE_URL}/api/customers/bulk")

        # Import with hooks enabled (default)
        form = aiohttp.FormData()
        form.add_field('file', csv_data, filename='test.csv', content_type='text/csv')

        async with session.post(f"{BASE_URL}/api/customers/import/csv", data=form) as resp:
            result = await resp.json()
            print(f"✅ Import with hooks: {result}")
            assert result['hooks_executed'] == True, "Hooks should be executed"
            # With validation hooks, invalid email should be skipped
            if result.get('skipped_records', 0) > 0:
                print(f"  - Skipped {result['skipped_records']} records due to validation")

async def test_csv_import_without_hooks():
    """Test CSV import with hooks disabled"""
    print("\n🧪 Testing CSV import WITHOUT hooks...")

    # Same CSV data
    csv_data = """name,email,phone,credit_limit,status
No Hook User 1,nohook1@example.com,555-1001,1500,active
No Hook User 2,nohook2@example.com,555-1002,2500,pending"""

    async with aiohttp.ClientSession() as session:
        # Import with hooks disabled
        form = aiohttp.FormData()
        form.add_field('file', csv_data, filename='test.csv', content_type='text/csv')

        async with session.post(
            f"{BASE_URL}/api/customers/import/csv?run_hooks=false",
            data=form
        ) as resp:
            result = await resp.json()
            print(f"✅ Import without hooks: {result}")
            assert result['hooks_executed'] == False, "Hooks should not be executed"

async def test_json_import_with_hooks():
    """Test JSON import with hooks enabled"""
    print("\n🧪 Testing JSON import WITH hooks...")

    # Create JSON backup data
    json_data = {
        "resource": "customers",
        "exported_at": "2025-09-19T18:00:00",
        "records": [
            {
                "name": "JSON User 1",
                "email": "json1@example.com",
                "phone": "555-2001",
                "credit_limit": "3000.00",
                "status": "active"
            },
            {
                "name": "JSON User 2",
                "email": "json2@example.com",
                "phone": "555-2002",
                "credit_limit": "4000.00",
                "status": "inactive"
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        # Import with hooks enabled (default)
        form = aiohttp.FormData()
        form.add_field('file', json.dumps(json_data), filename='test.json', content_type='application/json')

        async with session.post(f"{BASE_URL}/api/customers/import/json", data=form) as resp:
            result = await resp.json()
            print(f"✅ JSON import with hooks: {result}")
            assert result['hooks_executed'] == True, "Hooks should be executed"

async def test_json_import_skip_validation():
    """Test JSON import with validation skipped but other hooks enabled"""
    print("\n🧪 Testing JSON import with skip_validation=true...")

    # JSON data with potentially invalid email
    json_data = {
        "resource": "customers",
        "exported_at": "2025-09-19T18:00:00",
        "records": [
            {
                "name": "Skip Validation User",
                "email": "invalid-email-format",  # Normally would fail validation
                "phone": "555-3001",
                "credit_limit": "5000.00",
                "status": "active"
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        # Import with validation skipped
        form = aiohttp.FormData()
        form.add_field('file', json.dumps(json_data), filename='test.json', content_type='application/json')

        async with session.post(
            f"{BASE_URL}/api/customers/import/json?skip_validation=true",
            data=form
        ) as resp:
            result = await resp.json()
            print(f"✅ JSON import skip validation: {result}")
            assert result['hooks_executed'] == True, "Hooks should still be executed"
            # Non-validation hooks still run, just validation is skipped

async def test_get_imported_records():
    """Verify imported records"""
    print("\n🧪 Verifying imported records...")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/customers") as resp:
            data = await resp.json()
            print(f"✅ Total records in database: {data['total']}")

            # Check for records from different import methods
            names = [r['name'] for r in data['records']]

            csv_with_hooks = any('Test User' in n for n in names)
            csv_without_hooks = any('No Hook User' in n for n in names)
            json_with_hooks = any('JSON User' in n for n in names)
            json_skip_validation = any('Skip Validation User' in n for n in names)

            print(f"  - CSV import with hooks: {'✓' if csv_with_hooks else '✗'}")
            print(f"  - CSV import without hooks: {'✓' if csv_without_hooks else '✗'}")
            print(f"  - JSON import with hooks: {'✓' if json_with_hooks else '✗'}")
            print(f"  - JSON import skip validation: {'✓' if json_skip_validation else '✗'}")

async def test_export_and_reimport():
    """Test export and re-import cycle"""
    print("\n🧪 Testing export/re-import cycle...")

    async with aiohttp.ClientSession() as session:
        # Export current data as CSV
        async with session.get(f"{BASE_URL}/api/customers/export/csv") as resp:
            csv_content = await resp.text()
            print(f"✅ Exported {len(csv_content.splitlines())-1} records as CSV")

        # Export current data as JSON
        async with session.get(f"{BASE_URL}/api/customers/export/json") as resp:
            json_backup = await resp.json()
            record_count = len(json_backup['records'])
            print(f"✅ Exported {record_count} records as JSON backup")

        # Clear database
        await session.delete(f"{BASE_URL}/api/customers/bulk")
        print(f"✅ Cleared database")

        # Re-import JSON backup with hooks
        form = aiohttp.FormData()
        form.add_field('file', json.dumps(json_backup), filename='backup.json', content_type='application/json')

        async with session.post(f"{BASE_URL}/api/customers/import/json", data=form) as resp:
            result = await resp.json()
            print(f"✅ Re-imported backup: {result['imported_records']} records")
            assert result['imported_records'] == record_count, "Should restore all records"

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing Import/Export with Hook Execution")
    print("=" * 60)

    try:
        # Test CSV imports
        await test_csv_import_with_hooks()
        await test_csv_import_without_hooks()

        # Test JSON imports
        await test_json_import_with_hooks()
        await test_json_import_skip_validation()

        # Verify imported records
        await test_get_imported_records()

        # Test export/re-import cycle
        await test_export_and_reimport()

        print("\n" + "=" * 60)
        print("✅ All import/export tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())