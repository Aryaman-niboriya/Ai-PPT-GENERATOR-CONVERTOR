#!/usr/bin/env python3
"""
Script to fix dashboard data user mapping issue
- Remove email-based keys 
- Keep only user ID based keys
- Clean user-specific data isolation
"""

import json
import os

def clean_dashboard_data():
    """Clean up dashboard data to use only user IDs"""
    
    # Load users.json to get user mapping
    with open('users.json', 'r') as f:
        users = json.load(f)
    
    print("Users mapping:")
    for uid, user in users.items():
        print(f"  User ID {uid}: {user['email']}")
    
    # Load dashboard data
    with open('dashboard_data.json', 'r') as f:
        dashboard_data = json.load(f)
    
    print(f"\nOriginal dashboard data keys: {list(dashboard_data.keys())}")
    
    # Create clean dashboard data
    clean_data = {}
    
    # Keep only user ID based keys (numerical strings)
    for key, data in dashboard_data.items():
        if key.isdigit():  # Only keep numeric user IDs
            # Clean the data for this user
            clean_user_data = {
                'user_id': key,
                'email': users[key]['email'] if key in users else '',
                'total_presentations': data.get('total_presentations', 0),
                'total_conversions': data.get('total_conversions', 0), 
                'total_ai_generations': data.get('total_ai_generations', 0),
                'total_chat_sessions': data.get('total_chat_sessions', 0),
                'templates_used': data.get('templates_used', 0),
                'last_activity': data.get('last_activity'),
                'favorite_templates': data.get('favorite_templates', []),
                'recent_files': data.get('recent_files', [])
            }
            
            # Keep existing presentations if any
            if 'presentations' in data:
                clean_user_data['presentations'] = data['presentations']
                
            clean_data[key] = clean_user_data
            print(f"✓ Kept data for User ID {key}: {users[key]['email'] if key in users else 'Unknown'}")
        else:
            print(f"✗ Removed email-based key: {key}")
    
    # Backup original
    with open('dashboard_data_original.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Save clean data
    with open('dashboard_data.json', 'w') as f:
        json.dump(clean_data, f, indent=2)
    
    print(f"\nCleaned dashboard data keys: {list(clean_data.keys())}")
    print("✓ Dashboard data cleanup completed!")
    
    # Show summary
    print("\nSummary:")
    for uid, data in clean_data.items():
        user_email = users[uid]['email'] if uid in users else 'Unknown'
        print(f"  User {uid} ({user_email}):")
        print(f"    - Total presentations: {data['total_presentations']}")
        print(f"    - AI generations: {data['total_ai_generations']}")
        print(f"    - Conversions: {data['total_conversions']}")
        print(f"    - Templates used: {data['templates_used']}")
        print(f"    - Chat sessions: {data['total_chat_sessions']}")

if __name__ == '__main__':
    clean_dashboard_data()
