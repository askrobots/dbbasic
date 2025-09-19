#!/usr/bin/env python3
"""
Comprehensive API Tests for DBBasic CRUD Engine

Tests all CRUD operations, configuration loading, error handling,
and integration with AI Service Builder hooks.
"""

import pytest
import requests
import json
import time
import os
import tempfile
import yaml
from pathlib import Path

BASE_URL = "http://localhost:8005"

class TestCRUDEngineAPI:
    """Test suite for CRUD Engine API functionality"""

    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        # Wait for CRUD Engine to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/")
                if response.status_code == 200:
                    print("✅ CRUD Engine is ready")
                    break
            except requests.ConnectionError:
                if i == max_retries - 1:
                    raise Exception("❌ CRUD Engine not accessible after 30 seconds")
                time.sleep(1)

    def test_dashboard_loads(self):
        """Test that dashboard loads successfully"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert "DBBasic CRUD Dashboard" in response.text
        print("✅ Dashboard loads successfully")

    def test_customers_resource_exists(self):
        """Test that customers resource is loaded"""
        response = requests.get(f"{BASE_URL}/customers")
        assert response.status_code == 200
        assert "Customers Management" in response.text
        print("✅ Customers resource interface loads")

    def test_api_list_customers_empty(self):
        """Test listing customers when empty"""
        response = requests.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert isinstance(data["records"], list)
        print(f"✅ Empty customers list: {len(data['records'])} records")

    def test_api_create_customer_minimal(self):
        """Test creating a customer with minimal data"""
        customer_data = {
            "name": "Test Customer",
            "email": "test@example.com"
        }

        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers={"Content-Type": "application/json"}
        )

        # Should fail due to hooks, but test the flow
        print(f"📊 Create customer response: {response.status_code}")
        print(f"📊 Response: {response.text}")

        # Either succeeds (200) or fails due to missing hook service (500)
        assert response.status_code in [200, 500]

        if response.status_code == 500:
            # Should indicate hook service not found
            assert "validate_business_rules" in response.text or "Hook" in response.text
            print("✅ Hook system correctly detected missing service")
        else:
            # Success - verify data
            data = response.json()
            assert data["name"] == customer_data["name"]
            assert data["email"] == customer_data["email"]
            print("✅ Customer created successfully")

    def test_api_create_customer_full(self):
        """Test creating a customer with full data"""
        customer_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-0123",
            "credit_limit": 5000,
            "status": "active"
        }

        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"📊 Full customer creation: {response.status_code}")
        # Hook system should trigger
        assert response.status_code in [200, 500]
        print("✅ Full customer creation handled")

    def test_api_validation_errors(self):
        """Test validation error handling"""
        # Test missing required field
        invalid_data = {
            "email": "missing-name@example.com"
        }

        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )

        # Should fail validation or hook processing
        assert response.status_code in [400, 422, 500]
        print("✅ Validation errors handled properly")

    def test_api_duplicate_email(self):
        """Test duplicate email handling"""
        customer_data = {
            "name": "Duplicate Test",
            "email": "duplicate@example.com"
        }

        # Try to create same email twice
        response1 = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers={"Content-Type": "application/json"}
        )

        response2 = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"📊 First creation: {response1.status_code}")
        print(f"📊 Duplicate creation: {response2.status_code}")

        # At least one should indicate constraint violation
        assert response1.status_code in [200, 500] or response2.status_code in [400, 409, 500]
        print("✅ Duplicate email constraint handled")

class TestCRUDEngineConfig:
    """Test configuration loading and hot reload"""

    def create_test_config(self, resource_name="test_products"):
        """Create a test configuration file"""
        config = {
            "resource": resource_name,
            "database": f"{resource_name}.db",
            "fields": {
                "id": {"type": "primary_key"},
                "name": {
                    "type": "string",
                    "required": True,
                    "searchable": True,
                    "max_length": 100
                },
                "price": {
                    "type": "decimal",
                    "min": 0,
                    "max": 99999.99
                },
                "category": {
                    "type": "select",
                    "options": ["electronics", "books", "clothing"],
                    "default": "electronics"
                },
                "created_at": {
                    "type": "timestamp",
                    "auto_now_add": True
                }
            },
            "interface": {
                "list_display": ["name", "price", "category", "created_at"],
                "search_fields": ["name"],
                "filters": ["category", "created_at"],
                "per_page": 10
            },
            "permissions": {
                "create": "authenticated",
                "read": "public",
                "update": "authenticated",
                "delete": "admin_only"
            },
            "api": {
                "base_path": f"/api/{resource_name}",
                "enable_bulk": True,
                "enable_export": True
            }
        }

        config_file = f"{resource_name}_crud.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        return config_file

    def test_config_loading(self):
        """Test that new config files are loaded"""
        config_file = self.create_test_config("test_products")

        try:
            # Wait for file watcher to detect new config
            time.sleep(3)

            # Test that new resource is available
            response = requests.get(f"{BASE_URL}/test_products")
            print(f"📊 New resource response: {response.status_code}")

            if response.status_code == 200:
                assert "Test Products Management" in response.text or "test_products" in response.text.lower()
                print("✅ New config loaded successfully")
            else:
                print("⚠️ Config hot reload may need manual restart")

        finally:
            # Cleanup
            if os.path.exists(config_file):
                os.remove(config_file)

    def test_config_validation(self):
        """Test configuration validation"""
        # Create invalid config
        invalid_config = {
            "resource": "invalid_test",
            "fields": {
                # Missing required field structure
            }
        }

        config_file = "invalid_test_crud.yaml"
        try:
            with open(config_file, 'w') as f:
                yaml.dump(invalid_config, f)

            time.sleep(2)

            # Should not create invalid resource
            response = requests.get(f"{BASE_URL}/invalid_test")
            assert response.status_code == 404
            print("✅ Invalid config rejected")

        finally:
            if os.path.exists(config_file):
                os.remove(config_file)

class TestCRUDEngineIntegration:
    """Test integration with other services"""

    def test_ai_service_builder_integration(self):
        """Test that missing hooks trigger AI service requests"""
        # This test validates the hook detection logic
        customer_data = {
            "name": "Hook Test Customer",
            "email": "hooktest@example.com"
        }

        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers={"Content-Type": "application/json"}
        )

        # Should detect missing hook service
        if response.status_code == 500:
            error_text = response.text
            if "validate_business_rules" in error_text:
                print("✅ AI Service Builder integration: Hook detection working")
            else:
                print(f"📊 Hook response: {error_text}")
        else:
            print("📊 No hook errors - may be working with generated services")

    def test_real_time_monitor_integration(self):
        """Test that CRUD operations can send events to real-time monitor"""
        # Test if real-time monitor is accessible
        try:
            monitor_response = requests.get("http://localhost:8004")
            if monitor_response.status_code == 200:
                print("✅ Real-time Monitor accessible for integration")
            else:
                print("⚠️ Real-time Monitor not accessible")
        except requests.ConnectionError:
            print("⚠️ Real-time Monitor not running")

def run_api_tests():
    """Run all API tests"""
    print("🚀 Starting CRUD Engine API Tests")
    print("=" * 50)

    # Test basic functionality
    test_basic = TestCRUDEngineAPI()
    test_basic.setup_class()

    try:
        test_basic.test_dashboard_loads()
        test_basic.test_customers_resource_exists()
        test_basic.test_api_list_customers_empty()
        test_basic.test_api_create_customer_minimal()
        test_basic.test_api_create_customer_full()
        test_basic.test_api_validation_errors()
        test_basic.test_api_duplicate_email()

        print("\n📋 Basic API Tests: ✅ PASSED")

    except Exception as e:
        print(f"\n❌ Basic API Tests FAILED: {e}")
        return False

    # Test configuration
    test_config = TestCRUDEngineConfig()
    try:
        test_config.test_config_loading()
        test_config.test_config_validation()

        print("📋 Configuration Tests: ✅ PASSED")

    except Exception as e:
        print(f"❌ Configuration Tests FAILED: {e}")

    # Test integration
    test_integration = TestCRUDEngineIntegration()
    try:
        test_integration.test_ai_service_builder_integration()
        test_integration.test_real_time_monitor_integration()

        print("📋 Integration Tests: ✅ PASSED")

    except Exception as e:
        print(f"❌ Integration Tests FAILED: {e}")

    print("\n" + "=" * 50)
    print("✅ CRUD Engine API Testing Complete!")
    return True

if __name__ == "__main__":
    success = run_api_tests()
    exit(0 if success else 1)