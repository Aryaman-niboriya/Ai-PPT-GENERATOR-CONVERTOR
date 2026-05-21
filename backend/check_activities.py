from database import db_manager
import json
from datetime import datetime

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2, default=str))

def check_user_activities():
    """Check all user activities"""
    print("\n===== User Activities =====\n")
    
    # Get all user activities
    activities = list(db_manager.db.user_activities.find().limit(20))
    print(f"Total user activities: {db_manager.db.user_activities.count_documents({})}")
    print(f"Showing first {len(activities)} activities\n")
    
    # Check for fields in activities
    has_user_id = 0
    has_email = 0
    has_neither = 0
    
    for activity in activities:
        user_id = activity.get('user_id')
        email = activity.get('email')
        
        if user_id:
            has_user_id += 1
        if email:
            has_email += 1
        if not user_id and not email:
            has_neither += 1
    
    print(f"Activities with user_id: {has_user_id}")
    print(f"Activities with email: {has_email}")
    print(f"Activities with neither: {has_neither}")
    
    # Print sample activities
    print("\n--- Sample Activities ---\n")
    for i, activity in enumerate(activities[:5]):
        print(f"Activity {i+1}:")
        print(f"  User ID: {activity.get('user_id', 'N/A')}")
        print(f"  Email: {activity.get('email', 'N/A')}")
        print(f"  Type: {activity.get('activity_type', 'N/A')}")
        print(f"  Description: {activity.get('description', 'N/A')}")
        print(f"  Time: {activity.get('timestamp', 'N/A')}")
        print()
    
    # Check for any activities with specific user_id or email
    print("\n--- Checking for specific users ---\n")
    
    # Check for activities with user_id = "1" or "2"
    for user_id in ["1", "2"]:
        count = db_manager.db.user_activities.count_documents({"user_id": user_id})
        print(f"Activities with user_id '{user_id}': {count}")
    
    # Check for activities with specific emails
    for email in ["Kratika41@gmail.com", "aryamanniboriya94@gmail.com", "devansh21@gmail.com", "annu27@gmail.com"]:
        count = db_manager.db.user_activities.count_documents({"email": email})
        print(f"Activities with email '{email}': {count}")
        
        # If there are activities, show a sample
        if count > 0:
            print("  Sample activities:")
            sample_acts = list(db_manager.db.user_activities.find({"email": email}).limit(2))
            for act in sample_acts:
                print(f"    - {act.get('activity_type', 'N/A')}: {act.get('description', 'N/A')}")
            print()

def main():
    """Main function"""
    print("\n🔍 User Activities Inspector\n")
    check_user_activities()

if __name__ == "__main__":
    main()