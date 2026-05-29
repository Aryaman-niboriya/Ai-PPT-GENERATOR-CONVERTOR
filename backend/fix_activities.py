import os
from database import db_manager
from datetime import datetime

def fix_db():
    if db_manager.db is None:
        print("MongoDB is not connected!")
        return

    print("Fixing user_activities collection...")
    users = list(db_manager.db.users.find())
    email_to_uid = {user['email'].lower(): user.get('user_id') for user in users if 'email' in user}
    print(f"Loaded {len(users)} users from database.")

    # Fix activities
    activities = list(db_manager.db.user_activities.find())
    fixed_activities = 0
    for act in activities:
        updates = {}
        
        # 1. Map email to user_email
        email = act.get('email') or act.get('user_email')
        if email:
            email_lower = email.lower()
            if act.get('user_email') != email_lower:
                updates['user_email'] = email_lower
            if act.get('email') != email_lower:
                updates['email'] = email_lower
                
            # 2. Map user_id
            uid = email_to_uid.get(email_lower)
            if uid and act.get('user_id') != uid:
                updates['user_id'] = uid

        # 3. Map timestamp to activity_date
        timestamp = act.get('timestamp')
        if timestamp and 'activity_date' not in act:
            try:
                updates['activity_date'] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                updates['activity_date'] = datetime.utcnow()
        elif 'activity_date' not in act:
            updates['activity_date'] = datetime.utcnow()

        if updates:
            db_manager.db.user_activities.update_one({'_id': act['_id']}, {'$set': updates})
            fixed_activities += 1

    print(f"Fixed {fixed_activities} user activities.")

    # Fix chats
    chats = list(db_manager.db.chat_history.find())
    fixed_chats = 0
    for chat in chats:
        updates = {}
        email = chat.get('email') or chat.get('user_email')
        if email:
            email_lower = email.lower()
            if chat.get('user_email') != email_lower:
                updates['user_email'] = email_lower
            if chat.get('email') != email_lower:
                updates['email'] = email_lower
            
            uid = email_to_uid.get(email_lower)
            if uid and chat.get('user_id') != uid:
                updates['user_id'] = uid

        if updates:
            db_manager.db.chat_history.update_one({'_id': chat['_id']}, {'$set': updates})
            fixed_chats += 1

    print(f"Fixed {fixed_chats} chat history entries.")

if __name__ == "__main__":
    fix_db()
