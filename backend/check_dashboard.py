from database import db_manager
import json

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2, default=str))

def check_dashboard_data():
    """Check all dashboard data entries"""
    print("\n===== Dashboard Data =====\n")
    
    # Get all dashboard data
    dashboard_entries = list(db_manager.db.dashboard_data.find())
    print(f"Total dashboard entries: {len(dashboard_entries)}\n")
    
    for entry in dashboard_entries:
        user_id = entry.get('user_id', 'N/A')
        user_email = entry.get('user_email', 'N/A')
        
        print(f"Entry ID: {entry.get('_id')}")
        print(f"User ID: {user_id}")
        print(f"User Email: {user_email}")
        
        # Find user by ID or email
        user = None
        if user_id != 'N/A':
            user = db_manager.db.users.find_one({"user_id": user_id})
        if not user and user_email != 'N/A':
            user = db_manager.db.users.find_one({"email": user_email})
            
        if user:
            print(f"Associated Username: {user.get('username', 'N/A')}")
        else:
            print("No associated user found")
            
        # Print some dashboard stats
        if 'total_presentations' in entry:
            print(f"Total Presentations: {entry.get('total_presentations', 0)}")
        if 'total_ai_generations' in entry:
            print(f"Total AI Generations: {entry.get('total_ai_generations', 0)}")
        if 'total_chat_sessions' in entry:
            print(f"Total Chat Sessions: {entry.get('total_chat_sessions', 0)}")
            
        print("---\n")

def main():
    """Main function"""
    print("\n🔍 Dashboard Data Inspector\n")
    check_dashboard_data()

if __name__ == "__main__":
    main()