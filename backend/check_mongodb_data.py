from database import db_manager
import json

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2, default=str))

def count_documents():
    """Count documents in each collection"""
    print("\n===== Document Counts =====\n")
    print(f"Users: {db_manager.db.users.count_documents({})}")
    print(f"Dashboard Data: {db_manager.db.dashboard_data.count_documents({})}")
    print(f"User Activities: {db_manager.db.user_activities.count_documents({})}")
    print(f"Chat History: {db_manager.db.chat_history.count_documents({})}")

def list_users():
    """List all users in the database"""
    print("\n===== Users =====\n")
    users = list(db_manager.db.users.find())
    for user in users:
        print(f"User ID: {user.get('user_id', 'N/A')}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Username: {user.get('username', 'N/A')}")
        print("---")

def check_user_data(user_id):
    """Check data for a specific user"""
    print(f"\n===== Data for User ID: {user_id} =====\n")
    
    # Find user by ID
    user = db_manager.db.users.find_one({"user_id": user_id})
    if not user:
        print(f"No user found with ID: {user_id}")
        return
    
    print(f"Username: {user.get('username', 'N/A')}")
    print(f"Email: {user.get('email', 'N/A')}")
    
    # Check dashboard data
    dashboard_count = db_manager.db.dashboard_data.count_documents({"user_id": user_id})
    print(f"\nDashboard entries: {dashboard_count}")
    
    # Check user activities
    activities_count = db_manager.db.user_activities.count_documents({"user_id": user_id})
    print(f"User activities: {activities_count}")
    
    # Check chat history
    chat_count = db_manager.db.chat_history.count_documents({"user_id": user_id})
    print(f"Chat history entries: {chat_count}")
    
    # Show sample of user activities if any exist
    if activities_count > 0:
        print("\nSample user activities:")
        activities = list(db_manager.db.user_activities.find({"user_id": user_id}).limit(3))
        for activity in activities:
            print(f"  - {activity.get('activity_type', 'N/A')}: {activity.get('description', 'N/A')}")
            print(f"    Time: {activity.get('timestamp', 'N/A')}")

def main():
    """Main function"""
    print("\n🔍 MongoDB Data Inspector\n")
    
    # Count documents in collections
    count_documents()
    
    # List all users
    list_users()
    
    # Check data for specific users
    print("\n===== Checking Data Isolation =====\n")
    for user_id in ["1", "2", "3"]:
        check_user_data(user_id)

if __name__ == "__main__":
    main()