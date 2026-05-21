from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import logging

load_dotenv()

# Database configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pptcon_db")

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB database"""
        try:
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            print(f"✅ Connected to MongoDB database: {DATABASE_NAME}")
            
            # Initialize collections
            self.init_collections()
            
        except (ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print("💡 Make sure MongoDB is running: brew services start mongodb/brew/mongodb-community@7.0")
            print("💡 If using MongoDB Atlas, verify MONGODB_URI in .env from Atlas Connect > Drivers")
            self.client = None
            self.db = None
    
    def init_collections(self):
        """Initialize database collections with indexes"""
        if self.db is None:
            return
            
        # Users collection
        users_collection = self.db.users
        users_collection.create_index("email", unique=True)
        users_collection.create_index("username", unique=True)
        
        # Dashboard data collection
        dashboard_collection = self.db.dashboard_data
        dashboard_collection.create_index("user_email")
        dashboard_collection.create_index("date")
        
        # User activities collection
        activities_collection = self.db.user_activities
        activities_collection.create_index("user_email")
        activities_collection.create_index("activity_date")
        
        # Chat history collection
        chat_collection = self.db.chat_history
        chat_collection.create_index("user_email")
        chat_collection.create_index("timestamp")
        
        print("✅ Database collections initialized with indexes")
    
    def migrate_json_data(self):
        """Migrate existing JSON data to MongoDB"""
        if self.db is None:
            print("❌ Cannot migrate: Database not connected")
            return
            
        print("🔄 Starting data migration from JSON to MongoDB...")
        
        # Migrate users
        self.migrate_users()
        
        # Migrate dashboard data
        self.migrate_dashboard_data()
        
        # Migrate user activities
        self.migrate_user_activities()
        
        print("✅ Data migration completed!")
    
    def migrate_users(self):
        """Migrate users from JSON to MongoDB"""
        try:
            users_file = "users.json"
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                
                users_collection = self.db.users
                migrated_count = 0
                
                # Handle the actual JSON structure (dict with user IDs as keys)
                for user_id, user in users_data.items():
                    # Add migration timestamp and user_id
                    user_copy = user.copy()
                    user_copy['migrated_at'] = datetime.utcnow()
                    user_copy['user_id'] = user_id
                    
                    # Convert string date to datetime if needed
                    if isinstance(user_copy.get('created_at'), str):
                        try:
                            user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'].replace('Z', '+00:00'))
                        except:
                            user_copy['created_at'] = datetime.utcnow()
                    
                    # Insert or update user
                    users_collection.update_one(
                        {"email": user_copy['email']},
                        {"$set": user_copy},
                        upsert=True
                    )
                    migrated_count += 1
                print(f"✅ Migrated {migrated_count} users")
        except Exception as e:
            print(f"❌ Error migrating users: {e}")
            import traceback
            traceback.print_exc()
    
    def migrate_dashboard_data(self):
        """Migrate dashboard data from JSON to MongoDB"""
        try:
            dashboard_file = "dashboard_data.json"
            if os.path.exists(dashboard_file):
                with open(dashboard_file, 'r') as f:
                    dashboard_data = json.load(f)
                
                dashboard_collection = self.db.dashboard_data
                migrated_count = 0
                
                # Handle the actual JSON structure
                if isinstance(dashboard_data, dict):
                    # If it's a dict with user emails as keys
                    for user_email, entries in dashboard_data.items():
                        if isinstance(entries, list):
                            for entry in entries:
                                entry_copy = entry.copy()
                                entry_copy['migrated_at'] = datetime.utcnow()
                                entry_copy['user_email'] = user_email
                                
                                # Convert string date to datetime if needed
                                if isinstance(entry_copy.get('date'), str):
                                    try:
                                        entry_copy['date'] = datetime.fromisoformat(entry_copy['date'].replace('Z', '+00:00'))
                                    except:
                                        entry_copy['date'] = datetime.utcnow()
                                
                                dashboard_collection.insert_one(entry_copy)
                                migrated_count += 1
                        else:
                            # Single entry
                            entry_copy = entries.copy()
                            entry_copy['migrated_at'] = datetime.utcnow()
                            entry_copy['user_email'] = user_email
                            dashboard_collection.insert_one(entry_copy)
                            migrated_count += 1
                elif isinstance(dashboard_data, list):
                    # If it's a list of entries
                    for entry in dashboard_data:
                        entry_copy = entry.copy()
                        entry_copy['migrated_at'] = datetime.utcnow()
                        dashboard_collection.insert_one(entry_copy)
                        migrated_count += 1
                
                print(f"✅ Migrated {migrated_count} dashboard entries")
        except Exception as e:
            print(f"❌ Error migrating dashboard data: {e}")
            import traceback
            traceback.print_exc()
    
    def migrate_user_activities(self):
        """Migrate user activities from JSON to MongoDB"""
        try:
            activities_file = "user_activities.json"
            if os.path.exists(activities_file):
                with open(activities_file, 'r') as f:
                    activities_data = json.load(f)
                
                activities_collection = self.db.user_activities
                migrated_count = 0
                
                # Handle the actual JSON structure
                if isinstance(activities_data, dict):
                    # If it's a dict with user emails as keys
                    for user_email, activities in activities_data.items():
                        if isinstance(activities, list):
                            for activity in activities:
                                activity_copy = activity.copy()
                                activity_copy['migrated_at'] = datetime.utcnow()
                                activity_copy['user_email'] = user_email
                                
                                # Convert string date to datetime if needed
                                if isinstance(activity_copy.get('activity_date'), str):
                                    try:
                                        activity_copy['activity_date'] = datetime.fromisoformat(activity_copy['activity_date'].replace('Z', '+00:00'))
                                    except:
                                        activity_copy['activity_date'] = datetime.utcnow()
                                
                                activities_collection.insert_one(activity_copy)
                                migrated_count += 1
                        else:
                            # Single activity
                            activity_copy = activities.copy()
                            activity_copy['migrated_at'] = datetime.utcnow()
                            activity_copy['user_email'] = user_email
                            activities_collection.insert_one(activity_copy)
                            migrated_count += 1
                elif isinstance(activities_data, list):
                    # If it's a list of activities
                    for activity in activities_data:
                        activity_copy = activity.copy()
                        activity_copy['migrated_at'] = datetime.utcnow()
                        activities_collection.insert_one(activity_copy)
                        migrated_count += 1
                
                print(f"✅ Migrated {migrated_count} user activities")
        except Exception as e:
            print(f"❌ Error migrating user activities: {e}")
            import traceback
            traceback.print_exc()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        if self.db is None:
            return None
        return self.db.users.find_one({"email": email})
    
    def create_user(self, user_data):
        """Create new user"""
        if self.db is None:
            return None
        user_data['created_at'] = datetime.utcnow()
        result = self.db.users.insert_one(user_data)
        return result.inserted_id
    
    def update_user(self, email, update_data):
        """Update user data"""
        if self.db is None:
            return False
        update_data['updated_at'] = datetime.utcnow()
        result = self.db.users.update_one(
            {"email": email},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def save_dashboard_data(self, user_email, data):
        """Save dashboard data"""
        if self.db is None:
            return False
        # Get user_id from email
        user = self.get_user_by_email(user_email)
        if user and 'user_id' in user:
            data['user_id'] = user['user_id']
        data['user_email'] = user_email
        data['created_at'] = datetime.utcnow()
        result = self.db.dashboard_data.insert_one(data)
        return result.inserted_id
    
    def get_dashboard_data(self, user_email, limit=10):
        """Get dashboard data for user"""
        if self.db is None:
            return []
        # First try to find by user_id if available
        user = self.get_user_by_email(user_email)
        if user and 'user_id' in user:
            return list(self.db.dashboard_data.find(
                {"user_id": user['user_id']}
            ).sort("created_at", -1).limit(limit))
        # Fall back to email-based lookup if user_id not available
        return list(self.db.dashboard_data.find(
            {"user_email": user_email}
        ).sort("created_at", -1).limit(limit))
    
    def save_user_activity(self, user_email, activity_type, details=None):
        """Save user activity"""
        if self.db is None:
            return False
        # Get user_id from email
        user = self.get_user_by_email(user_email)
        activity = {
            "user_email": user_email,
            "activity_type": activity_type,
            "details": details or {},
            "activity_date": datetime.utcnow()
        }
        # Add user_id if available
        if user and 'user_id' in user:
            activity['user_id'] = user['user_id']
        result = self.db.user_activities.insert_one(activity)
        return result.inserted_id
    
    def get_user_activities(self, user_email, limit=50):
        """Get user activities"""
        if self.db is None:
            return []
        # First try to find by user_id if available
        user = self.get_user_by_email(user_email)
        if user and 'user_id' in user:
            return list(self.db.user_activities.find(
                {"user_id": user['user_id']}
            ).sort("activity_date", -1).limit(limit))
        # Fall back to email-based lookup if user_id not available
        return list(self.db.user_activities.find(
            {"user_email": user_email}
        ).sort("activity_date", -1).limit(limit))
    
    def save_chat_message(self, user_email, message, reply):
        """Save chat message"""
        if self.db is None:
            return False
        # Get user_id from email
        user = self.get_user_by_email(user_email)
        chat_entry = {
            "user_email": user_email,
            "message": message,
            "reply": reply,
            "timestamp": datetime.utcnow()
        }
        # Add user_id if available
        if user and 'user_id' in user:
            chat_entry['user_id'] = user['user_id']
        result = self.db.chat_history.insert_one(chat_entry)
        return result.inserted_id
    
    def get_chat_history(self, user_email, limit=20):
        """Get chat history"""
        if self.db is None:
            return []
        # First try to find by user_id if available
        user = self.get_user_by_email(user_email)
        if user and 'user_id' in user:
            return list(self.db.chat_history.find(
                {"user_id": user['user_id']}
            ).sort("timestamp", -1).limit(limit))
        # Fall back to email-based lookup if user_id not available
        return list(self.db.chat_history.find(
            {"user_email": user_email}
        ).sort("timestamp", -1).limit(limit))
    
    def close(self):
        """Close database connection"""
        if self.client is not None:
            self.client.close()
            print("🔌 Database connection closed")

# Global database instance
db_manager = DatabaseManager()
