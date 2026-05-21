#!/bin/bash

echo "\n===== MongoDB Data Inspection Commands =====\n"

echo "1. To view all users:"
echo "   python3 -c 'from database import db_manager; import json; docs = list(db_manager.db.users.find()); print(json.dumps([{**{k: str(v) if k=="_id" else v for k, v in d.items()}} for d in docs], indent=2))'"

echo "\n2. To view dashboard data for a specific user:"
echo "   python3 -c 'from database import db_manager; import json; docs = list(db_manager.db.dashboard_data.find({"user_id": "1"})); print(json.dumps([{**{k: str(v) if k=="_id" else v for k, v in d.items()}} for d in docs], indent=2))'"

echo "\n3. To view user activities for a specific user:"
echo "   python3 -c 'from database import db_manager; import json; docs = list(db_manager.db.user_activities.find({"user_id": "1"}).limit(5)); print(json.dumps([{**{k: str(v) if k=="_id" else v for k, v in d.items()}} for d in docs], indent=2))'"

echo "\n4. To view chat history for a specific user:"
echo "   python3 -c 'from database import db_manager; import json; docs = list(db_manager.db.chat_history.find({"user_id": "1"}).limit(5)); print(json.dumps([{**{k: str(v) if k=="_id" else v for k, v in d.items()}} for d in docs], indent=2))'"

echo "\n5. To count documents in each collection:"
echo "   python3 -c 'from database import db_manager; print("Users:", db_manager.db.users.count_documents({})); print("Dashboard Data:", db_manager.db.dashboard_data.count_documents({})); print("User Activities:", db_manager.db.user_activities.count_documents({})); print("Chat History:", db_manager.db.chat_history.count_documents({}))'"

echo "\n6. To check if a user's data is properly isolated:"
echo "   python3 -c 'from database import db_manager; user_id = "1"; print(f"Checking data isolation for user_id: {user_id}"); print(f"Dashboard entries: {db_manager.db.dashboard_data.count_documents({\"user_id\": user_id})}"); print(f"Activities: {db_manager.db.user_activities.count_documents({\"user_id\": user_id})}"); print(f"Chat history: {db_manager.db.chat_history.count_documents({\"user_id\": user_id})}")'"

echo "\n===== Usage =====\n"
echo "Copy and paste the desired command into the terminal to execute it."
echo "You can modify the user_id in commands 2-4 and 6 to check data for different users."