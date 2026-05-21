#!/usr/bin/env python3
"""
MongoDB Management Script for PPTCon
Use this script to manage your MongoDB database
"""

import os
import sys
from database import db_manager
from datetime import datetime
import json

def show_menu():
    print("\n🗄️  PPTCon MongoDB Manager")
    print("=" * 40)
    print("1. Show Database Statistics")
    print("2. List All Users")
    print("3. Show User Activities")
    print("4. Show Dashboard Data")
    print("5. Backup Database")
    print("6. Clear Database")
    print("7. Test Database Connection")
    print("8. Exit")
    print("=" * 40)

def show_statistics():
    """Show database statistics"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n📊 Database Statistics:")
    print("-" * 30)
    
    users_count = db_manager.db.users.count_documents({})
    dashboard_count = db_manager.db.dashboard_data.count_documents({})
    activities_count = db_manager.db.user_activities.count_documents({})
    chat_count = db_manager.db.chat_history.count_documents({})
    
    print(f"👥 Users: {users_count}")
    print(f"📈 Dashboard Entries: {dashboard_count}")
    print(f"📝 User Activities: {activities_count}")
    print(f"💬 Chat Messages: {chat_count}")

def list_users():
    """List all users"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n👥 All Users:")
    print("-" * 50)
    
    users = db_manager.db.users.find({}, {'password': 0, '_id': 0})
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
        print(f"   Created: {user.get('created_at', 'N/A')}")
        print(f"   Avatar: {user.get('avatar', 'None')}")
        print()

def show_activities():
    """Show recent user activities"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n📝 Recent User Activities:")
    print("-" * 50)
    
    # Query activities with user_id field first, then fall back to all activities
    activities = list(db_manager.db.user_activities.find({"user_id": {"$exists": True}}).sort("activity_date", -1).limit(10))
    
    # If no activities with user_id found, fall back to all activities
    if not activities:
        activities = list(db_manager.db.user_activities.find().sort("activity_date", -1).limit(10))
    
    for i, activity in enumerate(activities, 1):
        user_identifier = activity.get('user_id', activity.get('user_email', 'N/A'))
        print(f"{i}. User: {user_identifier}")
        print(f"   Activity: {activity.get('activity_type', 'N/A')}")
        print(f"   Date: {activity.get('activity_date', 'N/A')}")
        print()

def show_dashboard_data():
    """Show dashboard data"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n📈 Dashboard Data:")
    print("-" * 50)
    
    dashboard_data = db_manager.db.dashboard_data.find().sort("created_at", -1).limit(5)
    for i, entry in enumerate(dashboard_data, 1):
        print(f"{i}. User: {entry.get('user_email', 'N/A')}")
        print(f"   Type: {entry.get('type', 'N/A')}")
        print(f"   Date: {entry.get('date', 'N/A')}")
        print()

def backup_database():
    """Backup database to JSON files"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n💾 Creating Database Backup...")
    
    # Backup users
    users = list(db_manager.db.users.find({}, {'_id': 0}))
    with open('backup_users.json', 'w') as f:
        json.dump(users, f, indent=2, default=str)
    
    # Backup dashboard data
    dashboard_data = list(db_manager.db.dashboard_data.find({}, {'_id': 0}))
    with open('backup_dashboard.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    
    # Backup activities
    activities = list(db_manager.db.user_activities.find({}, {'_id': 0}))
    with open('backup_activities.json', 'w') as f:
        json.dump(activities, f, indent=2, default=str)
    
    print("✅ Backup created successfully!")
    print("📁 Files created:")
    print("   - backup_users.json")
    print("   - backup_dashboard.json")
    print("   - backup_activities.json")

def clear_database():
    """Clear all data from database"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    print("\n⚠️  WARNING: This will delete ALL data!")
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    
    if confirm == 'YES':
        db_manager.db.users.delete_many({})
        db_manager.db.dashboard_data.delete_many({})
        db_manager.db.user_activities.delete_many({})
        db_manager.db.chat_history.delete_many({})
        print("✅ Database cleared successfully!")
    else:
        print("❌ Operation cancelled")

def test_connection():
    """Test database connection"""
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    try:
        # Test basic operations
        db_manager.db.users.find_one()
        print("✅ Database connection test successful!")
        print("✅ Read operation: OK")
        print("✅ Write operation: OK")
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")

def main():
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            show_statistics()
        elif choice == '2':
            list_users()
        elif choice == '3':
            show_activities()
        elif choice == '4':
            show_dashboard_data()
        elif choice == '5':
            backup_database()
        elif choice == '6':
            clear_database()
        elif choice == '7':
            test_connection()
        elif choice == '8':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()


