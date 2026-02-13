#!/usr/bin/env python
"""
Script para testar a criação de usuário via API
Execute: python test_create_user_api.py
"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:3001"
TEST_EMAIL = f"test_{int(time.time())}@evoquefitness.test"
TEST_USERNAME = f"testuser{int(time.time())}"

def test_create_user():
    """Test creating a user via API"""
    print("\n" + "="*70)
    print("🧪 TESTING USER CREATION API")
    print("="*70)
    
    # Prepare user data
    user_data = {
        "nome": "Test",
        "sobrenome": "User",
        "usuario": TEST_USERNAME,
        "email": TEST_EMAIL,
        "nivel_acesso": "user",
        "setores": ["Portal de TI"],
        "alterar_senha_primeiro_acesso": True,
        "bloqueado": False
    }
    
    print(f"\n📝 Creating user with data:")
    print(f"   Email: {TEST_EMAIL}")
    print(f"   Username: {TEST_USERNAME}")
    print(f"   Name: {user_data['nome']} {user_data['sobrenome']}")
    
    try:
        # Make the request
        print(f"\n🔄 Sending POST request to {API_URL}/api/usuarios...")
        response = requests.post(
            f"{API_URL}/api/usuarios",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        # Handle response
        try:
            response_data = response.json()
            print(f"\n📦 Response data:")
            print(json.dumps(response_data, indent=2, default=str))
            
            if response.status_code == 200:
                print(f"\n✅ User created successfully!")
                print(f"   User ID: {response_data.get('id')}")
                print(f"   Auth0 Created: {response_data.get('auth0_created')}")
                print(f"   Auth0 ID: {response_data.get('auth0_id')}")
                print(f"   Password: {response_data.get('senha')}")
                
                if not response_data.get('auth0_created'):
                    print(f"\n⚠️  User created in database but NOT in Auth0")
                    print(f"   This usually means Auth0 M2M permissions are missing")
                    print(f"   Check if M2M app has 'create:users' permission")
            else:
                print(f"\n❌ Error (status {response.status_code}):")
                print(f"   Detail: {response_data.get('detail')}")
                
        except json.JSONDecodeError:
            print(f"\n❌ Could not parse response as JSON")
            print(f"   Response text: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {API_URL}")
        print(f"   Make sure backend is running on port 3001")
        print(f"   Run: python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_create_user()
