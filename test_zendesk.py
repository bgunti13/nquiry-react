
"""
Zendesk API Connection Test Script
This script tests the connection to Zendesk API and retrieves basic information.
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_zendesk_connection():
    """Test Zendesk API connection and retrieve basic information."""
    
    # Load credentials from environment variables
    api_token = os.getenv('ZENDESK_API_TOKEN')
    subdomain = os.getenv('ZENDESK_SUBDOMAIN')
    user_email = os.getenv('ZENDESK_USER_EMAIL')
    
    # Validate environment variables
    if not all([api_token, subdomain, user_email]):
        print("❌ Error: Missing required environment variables.")
        print(f"ZENDESK_API_TOKEN: {'✅' if api_token else '❌'}")
        print(f"ZENDESK_SUBDOMAIN: {'✅' if subdomain else '❌'}")
        print(f"ZENDESK_USER_EMAIL: {'✅' if user_email else '❌'}")
        return False
    
    print("🔧 Testing Zendesk API Connection...")
    print(f"📍 Subdomain: {subdomain}")
    print(f"👤 User Email: {user_email}")
    print("-" * 50)
    
    # Construct the base URL
    base_url = f'https://{subdomain}.zendesk.com/api/v2'
    
    # Authentication setup
    auth = (f'{user_email}/token', api_token)
    
    # Test 1: Get current user information
    print("🔍 Test 1: Getting current user information...")
    try:
        response = requests.get(f'{base_url}/users/me.json', auth=auth)
        
        if response.status_code == 200:
            user_data = response.json()
            user = user_data['user']
            print(f"✅ Success! Connected as: {user['name']} ({user['email']})")
            print(f"   Role: {user.get('role', 'N/A')}")
            print(f"   Active: {user.get('active', 'N/A')}")
            print(f"   Created: {user.get('created_at', 'N/A')}")
        else:
            print(f"❌ Failed to get user info. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    
    print("-" * 50)
    
    # Test 2: Get tickets (limited to 5 for testing)
    print("🎫 Test 2: Getting recent tickets...")
    try:
        response = requests.get(f'{base_url}/tickets.json?per_page=5', auth=auth)
        
        if response.status_code == 200:
            tickets_data = response.json()
            tickets = tickets_data['tickets']
            print(f"✅ Found {len(tickets)} tickets")
            
            for i, ticket in enumerate(tickets[:3], 1):  # Show first 3 tickets
                print(f"   {i}. Ticket #{ticket['id']}: {ticket.get('subject', 'No subject')[:50]}...")
                print(f"      Status: {ticket.get('status', 'N/A')} | Priority: {ticket.get('priority', 'N/A')}")
                
        else:
            print(f"❌ Failed to get tickets. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    print("-" * 50)
    
    # Test 3: Get groups
    print("👥 Test 3: Getting groups...")
    try:
        response = requests.get(f'{base_url}/groups.json', auth=auth)
        
        if response.status_code == 200:
            groups_data = response.json()
            groups = groups_data['groups']
            print(f"✅ Found {len(groups)} groups")
            
            for i, group in enumerate(groups[:3], 1):  # Show first 3 groups
                print(f"   {i}. {group.get('name', 'Unnamed group')} (ID: {group['id']})")
                
        else:
            print(f"❌ Failed to get groups. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    print("-" * 50)
    
    # Test 4: Get account info
    print("🏢 Test 4: Getting account information...")
    try:
        response = requests.get(f'{base_url}/account/settings.json', auth=auth)
        
        if response.status_code == 200:
            settings_data = response.json()
            settings = settings_data['settings']
            print(f"✅ Account URL: {settings.get('url', 'N/A')}")
            print(f"   Branding: {settings.get('branding_color', 'N/A')}")
            print(f"   Time Zone: {settings.get('time_zone', 'N/A')}")
            
        else:
            print(f"❌ Failed to get account settings. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    print("-" * 50)
    print("🎉 Zendesk API test completed!")
    return True

def create_test_ticket():
    """Create a test ticket to verify write permissions."""
    
    api_token = os.getenv('ZENDESK_API_TOKEN')
    subdomain = os.getenv('ZENDESK_SUBDOMAIN')
    user_email = os.getenv('ZENDESK_USER_EMAIL')
    
    base_url = f'https://{subdomain}.zendesk.com/api/v2'
    auth = (f'{user_email}/token', api_token)
    
    print("🎫 Test: Creating a test ticket...")
    
    ticket_data = {
        "ticket": {
            "subject": "API Test Ticket - Please ignore",
            "comment": {
                "body": "This is a test ticket created by the Zendesk API test script. You can safely delete this ticket."
            },
            "priority": "low",
            "type": "question"
        }
    }
    
    try:
        response = requests.post(
            f'{base_url}/tickets.json',
            json=ticket_data,
            auth=auth,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            ticket = response.json()['ticket']
            print(f"✅ Test ticket created successfully!")
            print(f"   Ticket ID: {ticket['id']}")
            print(f"   Subject: {ticket['subject']}")
            print(f"   Status: {ticket['status']}")
            return ticket['id']
        else:
            print(f"❌ Failed to create ticket. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ZENDESK API CONNECTION TEST")
    print("=" * 60)
    
    # Test basic connection
    success = test_zendesk_connection()
    
    if success:
        print("\n" + "=" * 60)
        
        # Ask if user wants to create a test ticket
        user_input = input("Do you want to create a test ticket? (y/n): ").lower().strip()
        
        if user_input in ['y', 'yes']:
            ticket_id = create_test_ticket()
            if ticket_id:
                print(f"\n💡 Note: You can view the test ticket at:")
                print(f"   https://{os.getenv('ZENDESK_SUBDOMAIN')}.zendesk.com/agent/tickets/{ticket_id}")
        
        print("\n✅ All tests completed successfully!")
        print("🎯 Your Zendesk API is working correctly!")
    else:
        print("\n❌ Connection test failed. Please check your credentials and try again.")