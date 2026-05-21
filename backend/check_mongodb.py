from database import db_manager
import json

def print_collection_data(collection_name, limit=10):
    """Print data from a MongoDB collection"""
    print(f"\n📄 Collection: {collection_name}")
    print("-" * 50)
    
    if db_manager.db is None:
        print("❌ Database not connected")
        return
    
    collection = db_manager.db[collection_name]
    count = collection.count_documents({})
    print(f"Total documents: {count}")
    
    if count == 0:
        print("No documents found.")
        return
    
    print(f"\nShowing first {min(limit, count)} documents:")
    documents = list(collection.find().limit(limit))
    
    for i, doc in enumerate(documents, 1):
        # Convert ObjectId to string for JSON serialization
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        # Pretty print the document
        print(f"\nDocument {i}:")
        print(json.dumps(doc, indent=2, default=str))

def main():
    """Main function to check MongoDB data"""
    print("🔍 MongoDB Data Check")
    
    # Check only users collection
    print_collection_data('users')
    
    # Check only dashboard_data collection
    print_collection_data('dashboard_data', limit=3)

if __name__ == "__main__":
    main()