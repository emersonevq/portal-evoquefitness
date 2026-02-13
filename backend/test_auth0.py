#!/usr/bin/env python
"""
Script para testar conexão e permissões do Auth0 M2M
Execute: python test_auth0.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Auth0 management client
from auth0.management import get_auth0_client
from auth0.config import (
    AUTH0_DOMAIN,
    AUTH0_M2M_CLIENT_ID,
    AUTH0_M2M_CLIENT_SECRET,
)

def test_auth0_connection():
    """Test Auth0 M2M connection and list users"""
    print("\n" + "="*70)
    print("🧪 AUTH0 M2M CONNECTION TEST")
    print("="*70)
    
    # Check configuration
    print("\n📋 Checking configuration...")
    print(f"   Domain: {AUTH0_DOMAIN}")
    print(f"   M2M Client ID: {AUTH0_M2M_CLIENT_ID[:20] + '...' if AUTH0_M2M_CLIENT_ID else '❌ NOT SET'}")
    print(f"   M2M Secret: {'✓ SET' if AUTH0_M2M_CLIENT_SECRET else '❌ NOT SET'}")
    
    if not AUTH0_M2M_CLIENT_ID or not AUTH0_M2M_CLIENT_SECRET:
        print("\n❌ ERROR: M2M credentials are not configured!")
        print("   Please set AUTH0_M2M_CLIENT_ID and AUTH0_M2M_CLIENT_SECRET in .env")
        return False
    
    try:
        # Get client and test token
        print("\n🔑 Getting M2M access token...")
        client = get_auth0_client()
        
        if not client.token:
            print("❌ Failed to get access token!")
            return False
        
        print("✅ Access token obtained successfully!")
        print(f"   Token (first 30 chars): {client.token[:30]}...")
        
        # Try to get users list
        print("\n👥 Testing: Get users list...")
        try:
            result = client.get_users(page=0, per_page=5)
            print(f"✅ Successfully retrieved users from Auth0!")
            print(f"   Users returned: {len(result.get('users', []))}")
        except Exception as e:
            print(f"❌ Failed to get users list: {e}")
            print("   This might indicate missing 'read:users' permission")
            return False
        
        # Try to create a test user
        print("\n👤 Testing: Create test user...")
        test_email = f"test_{int(__import__('time').time())}@evoquefitness.test"
        test_password = "TempPassword123!"
        
        try:
            new_user = client.create_user(
                email=test_email,
                password=test_password,
                given_name="Test",
                family_name="User"
            )
            print(f"✅ Test user created successfully!")
            print(f"   Email: {test_email}")
            print(f"   Auth0 ID: {new_user.get('user_id')}")
            
            # Try to delete the test user
            print("\n🗑️  Testing: Delete test user...")
            try:
                client.delete_user(new_user.get('user_id'))
                print(f"✅ Test user deleted successfully!")
            except Exception as e:
                print(f"⚠️  Could not delete test user: {e}")
                print(f"   (Not critical - you can delete manually in Auth0 Dashboard)")
            
        except Exception as e:
            print(f"❌ Failed to create test user: {e}")
            print("\n💡 Possible causes:")
            print("   1. Missing 'create:users' permission in M2M app")
            print("   2. Invalid password format (must have uppercase, lowercase, number, symbol)")
            print("   3. Email already exists in Auth0")
            return False
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED! Auth0 M2M is properly configured!")
        print("="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auth0_connection()
    sys.exit(0 if success else 1)
