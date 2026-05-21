#!/usr/bin/env python3
"""
Migration script to move data from JSON files to MongoDB
Run this script to migrate existing data to MongoDB
"""

import os
import sys
from database import db_manager
import json
from datetime import datetime

def main():
    print("🔄 Starting MongoDB Migration...")
    print("=" * 50)
    
    # Check if MongoDB is connected
    if db_manager.db is None:
        print("❌ MongoDB not connected. Please start MongoDB first:")
        print("   brew services start mongodb/brew/mongodb-community@7.0")
        return False
    
    print("✅ MongoDB connected successfully!")
    
    # Run migration
    try:
        db_manager.migrate_json_data()
        print("\n🎉 Migration completed successfully!")
        print("\n📊 Migration Summary:")
        print("- Users migrated to MongoDB")
        print("- Dashboard data migrated to MongoDB") 
        print("- User activities migrated to MongoDB")
        print("- Chat history will be saved to MongoDB going forward")
        
        # Show some stats
        users_count = db_manager.db.users.count_documents({})
        dashboard_count = db_manager.db.dashboard_data.count_documents({})
        activities_count = db_manager.db.user_activities.count_documents({})
        
        print(f"\n📈 Database Statistics:")
        print(f"- Total Users: {users_count}")
        print(f"- Dashboard Entries: {dashboard_count}")
        print(f"- User Activities: {activities_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ You can now use MongoDB for your PPTCon app!")
        print("💡 The app will automatically use MongoDB for new data")
        print("💡 Old JSON files are kept as backup")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
