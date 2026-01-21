"""
Setup Firebase Database for Tests

This script initializes Firestore with sample data for testing.
Run this after enabling Firestore API to prepare the database.

Usage:
    python setup_firebase_database.py              # Creates global test collections
    python setup_firebase_database.py --project 123  # Creates collections for project 123
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("\n[ERROR] firebase-admin not installed!")
    print("Install with: pip install firebase-admin")
    sys.exit(1)


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    print("=" * 80)
    print("FIREBASE DATABASE SETUP")
    print("=" * 80)

    key_path = Path(__file__).parent.parent / "dlovable-firebase-adminsdk-fbsvc-33ee906aab.json"

    if not key_path.exists():
        print(f"\n[ERROR] Service account key not found at: {key_path}")
        return None

    print(f"\n[OK] Found service account key")

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(key_path))
            firebase_admin.initialize_app(cred)
            print("[OK] Firebase Admin SDK initialized")

        db = firestore.client()
        print("[OK] Firestore client connected")
        print(f"[OK] Project: dlovable")

        return db

    except Exception as e:
        print(f"\n[ERROR] Failed to initialize Firebase: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_collection_name(project_id: int | None, base_name: str) -> str:
    """
    Get collection name with optional project scope

    Args:
        project_id: Project ID (None for global collections)
        base_name: Base collection name

    Returns:
        Collection name (project-scoped or global)
    """
    if project_id is None:
        return base_name
    return f"project_{project_id}_{base_name}"


def create_test_collections(db, project_id: int | None = None):
    """
    Create initial collections and sample data

    Args:
        db: Firestore client
        project_id: Optional project ID for scoped collections
    """
    print("\n" + "=" * 80)
    if project_id:
        print(f"CREATING TEST COLLECTIONS FOR PROJECT {project_id}")
    else:
        print("CREATING GLOBAL TEST COLLECTIONS")
    print("=" * 80)

    collections_created = []

    # Collection 1: Clients (for CRUD testing)
    collection_name = get_collection_name(project_id, 'clients')
    print(f"\n[1/5] Creating '{collection_name}' collection...")
    try:
        clients_data = [
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-0101",
                "company": "Acme Corp",
                "status": "active",
                "created_at": firestore.SERVER_TIMESTAMP,
                "tags": ["vip", "enterprise"],
                "metadata": {
                    "source": "website",
                    "industry": "technology"
                }
            },
            {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+1-555-0102",
                "company": "Tech Solutions",
                "status": "active",
                "created_at": firestore.SERVER_TIMESTAMP,
                "tags": ["partner"],
                "metadata": {
                    "source": "referral",
                    "industry": "finance"
                }
            },
            {
                "name": "Bob Johnson",
                "email": "bob.johnson@example.com",
                "phone": "+1-555-0103",
                "company": "Design Studio",
                "status": "inactive",
                "created_at": firestore.SERVER_TIMESTAMP,
                "tags": ["trial"],
                "metadata": {
                    "source": "marketing",
                    "industry": "creative"
                }
            }
        ]

        for i, client in enumerate(clients_data, 1):
            doc_ref = db.collection(collection_name).add(client)
            print(f"   Created client {i}: {client['name']} (ID: {doc_ref[1].id})")

        collections_created.append(collection_name)
        print(f"   [OK] Created '{collection_name}' collection with {len(clients_data)} documents")

    except Exception as e:
        print(f"   [ERROR] Failed to create clients: {e}")

    # Collection 2: Products (for inventory testing)
    collection_name = get_collection_name(project_id, 'products')
    print(f"\n[2/5] Creating '{collection_name}' collection...")
    try:
        products_data = [
            {
                "name": "Laptop Pro 15",
                "sku": "LAP-PRO-15",
                "price": 1299.99,
                "stock": 45,
                "category": "electronics",
                "description": "Professional laptop for developers",
                "created_at": firestore.SERVER_TIMESTAMP,
                "specifications": {
                    "ram": "16GB",
                    "storage": "512GB SSD",
                    "processor": "Intel i7"
                }
            },
            {
                "name": "Wireless Mouse",
                "sku": "MSE-WRL-01",
                "price": 29.99,
                "stock": 150,
                "category": "accessories",
                "description": "Ergonomic wireless mouse",
                "created_at": firestore.SERVER_TIMESTAMP,
                "specifications": {
                    "battery": "AAA x2",
                    "connectivity": "Bluetooth 5.0"
                }
            },
            {
                "name": "USB-C Hub",
                "sku": "HUB-USC-08",
                "price": 49.99,
                "stock": 0,
                "category": "accessories",
                "description": "8-in-1 USB-C hub",
                "created_at": firestore.SERVER_TIMESTAMP,
                "specifications": {
                    "ports": "8",
                    "power_delivery": "100W"
                }
            }
        ]

        for i, product in enumerate(products_data, 1):
            doc_ref = db.collection(collection_name).add(product)
            print(f"   Created product {i}: {product['name']} (${product['price']})")

        collections_created.append(collection_name)
        print(f"   [OK] Created '{collection_name}' collection with {len(products_data)} documents")

    except Exception as e:
        print(f"   [ERROR] Failed to create products: {e}")

    # Collection 3: Orders (for transaction testing)
    collection_name = get_collection_name(project_id, 'orders')
    print(f"\n[3/5] Creating '{collection_name}' collection...")
    try:
        orders_data = [
            {
                "order_number": "ORD-2024-001",
                "customer_id": "client_001",
                "customer_name": "John Doe",
                "items": [
                    {"product": "Laptop Pro 15", "quantity": 1, "price": 1299.99},
                    {"product": "Wireless Mouse", "quantity": 2, "price": 29.99}
                ],
                "total": 1359.97,
                "status": "shipped",
                "created_at": firestore.SERVER_TIMESTAMP,
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94105"
                }
            },
            {
                "order_number": "ORD-2024-002",
                "customer_id": "client_002",
                "customer_name": "Jane Smith",
                "items": [
                    {"product": "USB-C Hub", "quantity": 3, "price": 49.99}
                ],
                "total": 149.97,
                "status": "pending",
                "created_at": firestore.SERVER_TIMESTAMP,
                "shipping_address": {
                    "street": "456 Oak Ave",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001"
                }
            }
        ]

        for i, order in enumerate(orders_data, 1):
            doc_ref = db.collection(collection_name).add(order)
            print(f"   Created order {i}: {order['order_number']} (${order['total']})")

        collections_created.append(collection_name)
        print(f"   [OK] Created '{collection_name}' collection with {len(orders_data)} documents")

    except Exception as e:
        print(f"   [ERROR] Failed to create orders: {e}")

    # Collection 4: Users (for authentication testing)
    collection_name = get_collection_name(project_id, 'users')
    print(f"\n[4/5] Creating '{collection_name}' collection...")
    try:
        users_data = [
            {
                "username": "admin",
                "email": "admin@dlovable.com",
                "role": "admin",
                "display_name": "Administrator",
                "created_at": firestore.SERVER_TIMESTAMP,
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "notifications": True
                }
            },
            {
                "username": "developer",
                "email": "dev@dlovable.com",
                "role": "developer",
                "display_name": "Developer User",
                "created_at": firestore.SERVER_TIMESTAMP,
                "preferences": {
                    "theme": "light",
                    "language": "es",
                    "notifications": False
                }
            }
        ]

        for i, user in enumerate(users_data, 1):
            doc_ref = db.collection(collection_name).add(user)
            print(f"   Created user {i}: {user['username']} ({user['role']})")

        collections_created.append(collection_name)
        print(f"   [OK] Created '{collection_name}' collection with {len(users_data)} documents")

    except Exception as e:
        print(f"   [ERROR] Failed to create users: {e}")

    # Collection 5: Settings (for configuration testing)
    collection_name = get_collection_name(project_id, 'settings')
    print(f"\n[5/5] Creating '{collection_name}' collection...")
    try:
        settings_data = [
            {
                "key": "app_config",
                "name": "Application Configuration",
                "data": {
                    "app_name": "DaveLovable",
                    "version": "1.0.0",
                    "maintenance_mode": False,
                    "max_upload_size": 10485760,  # 10MB
                    "allowed_file_types": ["jpg", "png", "pdf", "doc"]
                },
                "updated_at": firestore.SERVER_TIMESTAMP
            },
            {
                "key": "email_config",
                "name": "Email Configuration",
                "data": {
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "from_email": "noreply@dlovable.com",
                    "templates": {
                        "welcome": "Welcome to DaveLovable!",
                        "password_reset": "Reset your password"
                    }
                },
                "updated_at": firestore.SERVER_TIMESTAMP
            }
        ]

        for i, setting in enumerate(settings_data, 1):
            doc_ref = db.collection(collection_name).document(setting['key']).set(setting)
            print(f"   Created setting {i}: {setting['name']}")

        collections_created.append(collection_name)
        print(f"   [OK] Created '{collection_name}' collection with {len(settings_data)} documents")

    except Exception as e:
        print(f"   [ERROR] Failed to create settings: {e}")

    return collections_created


def verify_database(db, project_id: int | None = None):
    """
    Verify all collections were created successfully

    Args:
        db: Firestore client
        project_id: Optional project ID for scoped collections
    """
    print("\n" + "=" * 80)
    print("VERIFYING DATABASE")
    print("=" * 80)

    base_collections = ['clients', 'products', 'orders', 'users', 'settings']

    for base_name in base_collections:
        collection_name = get_collection_name(project_id, base_name)
        try:
            docs = list(db.collection(collection_name).limit(1).stream())
            if docs:
                print(f"[OK] {collection_name.ljust(35)} - Found documents")
            else:
                print(f"[WARNING] {collection_name.ljust(35)} - Empty collection")
        except Exception as e:
            print(f"[ERROR] {collection_name.ljust(35)} - {e}")


def create_indexes(db):
    """Information about creating indexes"""
    print("\n" + "=" * 80)
    print("INDEXES INFORMATION")
    print("=" * 80)

    print("\n[INFO] Firestore automatically creates single-field indexes.")
    print("[INFO] For complex queries, you may need composite indexes.")
    print("\nRecommended indexes to create manually in Firebase Console:")
    print("\n1. Clients by status and created_at:")
    print("   Collection: clients")
    print("   Fields: status (Ascending), created_at (Descending)")
    print("\n2. Products by category and price:")
    print("   Collection: products")
    print("   Fields: category (Ascending), price (Ascending)")
    print("\n3. Orders by status and created_at:")
    print("   Collection: orders")
    print("   Fields: status (Ascending), created_at (Descending)")
    print("\nCreate indexes at:")
    print("https://console.firebase.google.com/project/dlovable/firestore/indexes")


def display_summary(collections_created, project_id: int | None = None):
    """
    Display final summary

    Args:
        collections_created: List of created collection names
        project_id: Optional project ID for scoped collections
    """
    print("\n" + "=" * 80)
    print("SETUP COMPLETE")
    print("=" * 80)

    if project_id:
        print(f"\n[SUCCESS] Created {len(collections_created)} collections for PROJECT {project_id}:")
    else:
        print(f"\n[SUCCESS] Created {len(collections_created)} GLOBAL collections:")

    for i, collection in enumerate(collections_created, 1):
        print(f"   {i}. {collection}")

    print("\nDatabase Statistics:")
    print("   - Total Collections: 5")
    print("   - Sample Clients: 3")
    print("   - Sample Products: 3")
    print("   - Sample Orders: 2")
    print("   - Sample Users: 2")
    print("   - Sample Settings: 2")
    print("   - Total Documents: ~12")

    if project_id:
        print(f"\nProject Scope:")
        print(f"   - All collections are isolated for project {project_id}")
        print(f"   - Collection naming pattern: project_{project_id}_<name>")
        print(f"   - Other projects won't see or access this data")

    print("\nNext Steps:")
    print("   1. Run tests: python test/test_firebase_real_connection.py")
    print("   2. View data: https://console.firebase.google.com/project/dlovable/firestore")
    print("   3. Configure security rules for production")
    print("   4. Create composite indexes for complex queries")

    print("\nFirebase Console:")
    print("   https://console.firebase.google.com/project/dlovable")

    print("\n" + "=" * 80)


def main():
    """Main setup function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Setup Firebase database with test data')
    parser.add_argument('--project', '-p', type=int, default=None,
                       help='Project ID for scoped collections (optional)')
    args = parser.parse_args()

    project_id = args.project

    # Initialize Firebase
    db = initialize_firebase()
    if not db:
        print("\n[FAILED] Could not initialize Firebase")
        return False

    # Create collections
    collections_created = create_test_collections(db, project_id)

    if not collections_created:
        print("\n[FAILED] No collections were created")
        return False

    # Verify database
    verify_database(db, project_id)

    # Show index information
    create_indexes(db)

    # Display summary
    display_summary(collections_created, project_id)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
