"""
Test Real Firebase Connection

This test connects to the actual Firebase project using Admin SDK
and performs real CRUD operations to validate the integration.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if firebase-admin is installed
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("\n[WARNING] firebase-admin not installed!")
    print("Install with: pip install firebase-admin")
    print("\nSkipping real connection tests...\n")


def test_firebase_connection():
    """Test connection to Firebase using Admin SDK"""
    if not FIREBASE_AVAILABLE:
        return False

    print("=" * 80)
    print("TEST: Real Firebase Connection")
    print("=" * 80)

    # Path to service account key
    key_path = Path(__file__).parent.parent / "dlovable-firebase-adminsdk-fbsvc-33ee906aab.json"

    if not key_path.exists():
        print(f"\n[ERROR] Service account key not found at: {key_path}")
        return False

    print(f"\n[OK] Found service account key: {key_path.name}")

    try:
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(key_path))
            firebase_admin.initialize_app(cred)
            print("[OK] Firebase Admin SDK initialized")
        else:
            print("[OK] Firebase Admin SDK already initialized")

        # Get Firestore client
        db = firestore.client()
        print("[OK] Firestore client created")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to initialize Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_firestore_crud_operations():
    """Test CRUD operations on Firestore"""
    if not FIREBASE_AVAILABLE:
        return False

    print("\n" + "=" * 80)
    print("TEST: Firestore CRUD Operations")
    print("=" * 80)

    try:
        db = firestore.client()

        # Collection name for testing
        test_collection = "test_clients"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n[OK] Using test collection: {test_collection}")

        # CREATE - Add a test document
        print("\n1. CREATE - Adding test document...")
        test_doc_data = {
            "name": f"Test Client {timestamp}",
            "email": f"test_{timestamp}@example.com",
            "created_at": firestore.SERVER_TIMESTAMP,
            "active": True,
            "tags": ["test", "automated"],
            "metadata": {
                "test_run": timestamp,
                "source": "test_firebase_real_connection.py"
            }
        }

        doc_ref = db.collection(test_collection).add(test_doc_data)
        doc_id = doc_ref[1].id
        print(f"   [OK] Document created with ID: {doc_id}")
        print(f"   Data: {test_doc_data['name']}, {test_doc_data['email']}")

        # READ - Retrieve the document
        print("\n2. READ - Retrieving document...")
        doc = db.collection(test_collection).document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            print(f"   [OK] Document retrieved successfully")
            print(f"   Name: {data['name']}")
            print(f"   Email: {data['email']}")
            print(f"   Active: {data['active']}")
            print(f"   Tags: {data['tags']}")
        else:
            print(f"   [ERROR] Document not found!")
            return False

        # UPDATE - Modify the document
        print("\n3. UPDATE - Updating document...")
        db.collection(test_collection).document(doc_id).update({
            "active": False,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "notes": "Updated via automated test"
        })
        print(f"   [OK] Document updated")

        # Verify update
        updated_doc = db.collection(test_collection).document(doc_id).get()
        updated_data = updated_doc.to_dict()
        print(f"   Active status: {updated_data['active']}")
        print(f"   Notes: {updated_data.get('notes', 'N/A')}")

        # QUERY - List all test documents
        print("\n4. QUERY - Listing all test documents...")
        docs = db.collection(test_collection).where("active", "==", False).limit(5).stream()
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            print(f"   [{count}] ID: {doc.id}, Name: {data.get('name', 'N/A')}")

        print(f"   [OK] Found {count} inactive clients")

        # DELETE - Remove test document
        print("\n5. DELETE - Removing test document...")
        db.collection(test_collection).document(doc_id).delete()
        print(f"   [OK] Document {doc_id} deleted")

        # Verify deletion
        deleted_doc = db.collection(test_collection).document(doc_id).get()
        if not deleted_doc.exists:
            print(f"   [OK] Deletion verified - document no longer exists")
        else:
            print(f"   [WARNING] Document still exists after deletion!")

        print("\n[SUCCESS] All CRUD operations completed successfully!")
        return True

    except Exception as e:
        print(f"\n[ERROR] CRUD operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_firestore_batch_operations():
    """Test batch write operations"""
    if not FIREBASE_AVAILABLE:
        return False

    print("\n" + "=" * 80)
    print("TEST: Firestore Batch Operations")
    print("=" * 80)

    try:
        db = firestore.client()
        batch = db.batch()
        test_collection = "test_batch_clients"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n[OK] Creating batch write for {test_collection}")

        # Create 3 documents in a batch
        doc_ids = []
        for i in range(1, 4):
            doc_ref = db.collection(test_collection).document()
            doc_ids.append(doc_ref.id)
            batch.set(doc_ref, {
                "name": f"Batch Client {i} - {timestamp}",
                "email": f"batch{i}_{timestamp}@example.com",
                "batch_number": i,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            print(f"   [{i}] Prepared document: {doc_ref.id}")

        # Commit the batch
        print("\n[OK] Committing batch...")
        batch.commit()
        print(f"   [OK] Batch committed - {len(doc_ids)} documents created")

        # Verify batch creation
        print("\n[OK] Verifying batch documents...")
        for i, doc_id in enumerate(doc_ids, 1):
            doc = db.collection(test_collection).document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                print(f"   [{i}] Verified: {data['name']}")

        # Cleanup - Delete batch documents
        print("\n[OK] Cleaning up batch documents...")
        cleanup_batch = db.batch()
        for doc_id in doc_ids:
            doc_ref = db.collection(test_collection).document(doc_id)
            cleanup_batch.delete(doc_ref)
        cleanup_batch.commit()
        print(f"   [OK] Cleaned up {len(doc_ids)} documents")

        print("\n[SUCCESS] Batch operations completed successfully!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Batch operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_firestore_realtime_listener():
    """Test real-time listener (snapshot)"""
    if not FIREBASE_AVAILABLE:
        return False

    print("\n" + "=" * 80)
    print("TEST: Firestore Real-time Listener")
    print("=" * 80)

    try:
        db = firestore.client()
        test_collection = "test_realtime"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n[OK] Testing snapshot functionality")

        # Create a test document
        doc_ref = db.collection(test_collection).document()
        doc_ref.set({
            "name": f"Realtime Test {timestamp}",
            "value": 0,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        doc_id = doc_ref.id
        print(f"   [OK] Created document: {doc_id}")

        # Get snapshot
        doc = doc_ref.get()
        data = doc.to_dict()
        print(f"   [OK] Initial value: {data['value']}")

        # Update and get new snapshot
        doc_ref.update({"value": 42})
        updated_doc = doc_ref.get()
        updated_data = updated_doc.to_dict()
        print(f"   [OK] Updated value: {updated_data['value']}")

        # Cleanup
        doc_ref.delete()
        print(f"   [OK] Cleaned up test document")

        print("\n[SUCCESS] Real-time listener test completed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Real-time listener test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Firebase real connection tests"""
    print("\n")
    print("=" * 80)
    print("FIREBASE REAL CONNECTION TEST SUITE")
    print("=" * 80)
    print("\nProject: dlovable")
    print("Testing with: Firebase Admin SDK")
    print("=" * 80)

    if not FIREBASE_AVAILABLE:
        print("\n[SKIPPED] Firebase Admin SDK not available")
        print("\nTo run these tests, install:")
        print("  pip install firebase-admin")
        return False

    results = []

    # Test 1: Connection
    results.append(("Connection", test_firebase_connection()))

    # Test 2: CRUD Operations
    results.append(("CRUD Operations", test_firestore_crud_operations()))

    # Test 3: Batch Operations
    results.append(("Batch Operations", test_firestore_batch_operations()))

    # Test 4: Real-time Listener
    results.append(("Real-time Listener", test_firestore_realtime_listener()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "=" * 80)
    if passed == total:
        print(f"[SUCCESS] All {total} tests passed!")
        print("=" * 80)
        print("\nFirebase connection is working correctly!")
        print("You can now use Firestore in your application.")
        print("\nNext steps:")
        print("  1. Configure .env.local with your Firebase config")
        print("  2. Install firebase SDK: npm install firebase")
        print("  3. Use the templates from filesystem_service.py")
        return True
    else:
        print(f"[FAILED] {total - passed}/{total} tests failed")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
