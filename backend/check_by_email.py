from database import db_manager
import json

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2, default=str))

def check_user_data_by_email(email):
    """Check data for a specific user by email"""
    print(f"\n===== Data for User Email: {email} =====\n")
    
    # Find user by email
    user = db_manager.db.users.find_one({"email": email})
    if not user:
        print(f"No user found with email: {email}")
        return
    
    print(f"Username: {user.get('username', 'N/A')}")
    print(f"User ID: {user.get('user_id', 'N/A')}")
    
    # Check dashboard data by email
    dashboard_by_email = list(db_manager.db.dashboard_data.find({"user_email": email}))
    print(f"\nDashboard entries by email: {len(dashboard_by_email)}")
    
    # Check user activities by email
    activities_by_email = list(db_manager.db.user_activities.find({"email": email}))
    print(f"User activities by email: {len(activities_by_email)}")
    
    # Check chat history by email
    chat_by_email = list(db_manager.db.chat_history.find({"email": email}))
    print(f"Chat history entries by email: {len(chat_by_email)}")
    
    # Show sample of user activities if any exist
    if activities_by_email:
        print("\nSample user activities:")
        for activity in activities_by_email[:3]:
            print(f"  - {activity.get('activity_type', 'N/A')}: {activity.get('description', 'N/A')}")
            print(f"    Time: {activity.get('timestamp', 'N/A')}")
            print(f"    User ID: {activity.get('user_id', 'N/A')}")

def main():
    """Main function"""
    print("\n🔍 MongoDB Data Inspector (By Email)\n")
    
    # Get all users
    users = list(db_manager.db.users.find())
    
    # Check data for each user by email
    for user in users:
        email = user.get('email')
        if email:
            check_user_data_by_email(email)

if __name__ == "__main__":
    main()