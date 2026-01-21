"""
Create Firestore Database Programmatically

This script creates a Firestore database using Google Cloud API.
Alternative to creating it manually in Firebase Console.
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.cloud import firestore_admin_v1
    from google.api_core import exceptions
    ADMIN_API_AVAILABLE = True
except ImportError:
    ADMIN_API_AVAILABLE = False
    print("\n[ERROR] google-cloud-firestore-admin not installed!")
    print("Install with: pip install google-cloud-firestore-admin")
    sys.exit(1)


def create_firestore_database():
    """Create Firestore database using Admin API"""
    print("=" * 80)
    print("CREATE FIRESTORE DATABASE PROGRAMMATICALLY")
    print("=" * 80)

    # Service account key path
    key_path = Path(__file__).parent.parent / "dlovable-firebase-adminsdk-fbsvc-33ee906aab.json"

    if not key_path.exists():
        print(f"\n[ERROR] Service account key not found at: {key_path}")
        return False

    print(f"\n[OK] Found service account key")

    # Set credentials environment variable
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(key_path)

    try:
        # Create Firestore Admin client
        client = firestore_admin_v1.FirestoreAdminClient()
        print("[OK] Firestore Admin client created")

        # Project info
        project_id = "dlovable"
        location_id = "us-central1"  # Change if needed
        database_id = "(default)"

        # Create database request
        parent = f"projects/{project_id}"

        print(f"\n[INFO] Creating Firestore database...")
        print(f"   Project: {project_id}")
        print(f"   Location: {location_id}")
        print(f"   Database: {database_id}")

        # Database configuration
        database = firestore_admin_v1.Database(
            name=f"{parent}/databases/{database_id}",
            location_id=location_id,
            type_=firestore_admin_v1.Database.DatabaseType.FIRESTORE_NATIVE,
            concurrency_mode=firestore_admin_v1.Database.ConcurrencyMode.OPTIMISTIC,
        )

        # Create the database
        operation = client.create_database(
            parent=parent,
            database=database,
            database_id=database_id,
        )

        print("\n[INFO] Database creation started...")
        print("[INFO] Waiting for operation to complete (this may take 1-2 minutes)...")

        # Wait for operation to complete
        result = operation.result(timeout=180)

        print("\n[SUCCESS] Firestore database created!")
        print(f"[OK] Database name: {result.name}")
        print(f"[OK] Location: {result.location_id}")
        print(f"[OK] Type: {result.type_.name}")

        return True

    except exceptions.AlreadyExists:
        print("\n[OK] Firestore database already exists!")
        print("[INFO] You can proceed with the setup script.")
        return True

    except exceptions.PermissionDenied as e:
        print("\n[ERROR] Permission denied!")
        print("\nThis can happen for two reasons:")
        print("1. Service account lacks 'Firebase Admin' or 'Cloud Datastore Owner' role")
        print("2. Firebase needs to be enabled in the project first")
        print("\nManual steps required:")
        print("1. Go to: https://console.firebase.google.com/project/dlovable")
        print("2. Accept Firebase terms if prompted")
        print("3. Then go to: https://console.firebase.google.com/project/dlovable/firestore")
        print("4. Click 'Create database'")
        print("\nError details:", str(e))
        return False

    except exceptions.FailedPrecondition as e:
        print("\n[INFO] Cannot create database programmatically")
        print("\nFirebase requires you to create the first Firestore database")
        print("through the Firebase Console for security reasons.")
        print("\nPlease follow these steps:")
        print("\n1. Go to: https://console.firebase.google.com/project/dlovable/firestore")
        print("2. Click 'Create database'")
        print("3. Select 'Start in test mode'")
        print("4. Choose location: us-central1 (or your preference)")
        print("5. Click 'Enable'")
        print("\nAfter that, run the setup script:")
        print("   python test/setup_firebase_database.py")
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def enable_firestore_api():
    """Enable Firestore API using Service Usage API"""
    print("\n" + "=" * 80)
    print("ENABLING FIRESTORE API")
    print("=" * 80)

    try:
        from google.cloud import service_usage_v1

        key_path = Path(__file__).parent.parent / "dlovable-firebase-adminsdk-fbsvc-33ee906aab.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(key_path)

        client = service_usage_v1.ServiceUsageClient()
        project_id = "dlovable"

        # Enable Firestore API
        service_name = f"projects/{project_id}/services/firestore.googleapis.com"

        print(f"\n[INFO] Enabling Firestore API for project: {project_id}")

        request = service_usage_v1.EnableServiceRequest(
            name=service_name
        )

        operation = client.enable_service(request=request)
        print("[INFO] Waiting for API to be enabled...")

        result = operation.result(timeout=60)

        print("[SUCCESS] Firestore API enabled!")
        return True

    except exceptions.AlreadyExists:
        print("[OK] Firestore API already enabled")
        return True

    except ImportError:
        print("\n[INFO] google-cloud-service-usage not installed")
        print("Install with: pip install google-cloud-service-usage")
        print("\nAlternatively, enable manually:")
        print("https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=dlovable")
        return False

    except Exception as e:
        print(f"\n[ERROR] Could not enable API: {e}")
        return False


def main():
    """Main function"""
    print("\n")

    # Step 1: Try to enable API
    print("STEP 1: Enable Firestore API")
    print("-" * 80)
    api_enabled = enable_firestore_api()

    if api_enabled:
        print("\n[OK] API is enabled, waiting 10 seconds for propagation...")
        import time
        time.sleep(10)

    # Step 2: Try to create database
    print("\n" + "=" * 80)
    print("STEP 2: Create Firestore Database")
    print("-" * 80)
    db_created = create_firestore_database()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if db_created:
        print("\n[SUCCESS] Firestore is ready!")
        print("\nNext steps:")
        print("1. Run: python test/setup_firebase_database.py")
        print("2. Run: python test/test_firebase_real_connection.py")
        return True
    else:
        print("\n[ACTION REQUIRED] Manual setup needed")
        print("\nQuick setup (2 minutes):")
        print("1. Open: https://console.firebase.google.com/project/dlovable/firestore")
        print("2. Click 'Create database'")
        print("3. Choose 'Start in test mode'")
        print("4. Select location: us-central1")
        print("5. Click 'Enable'")
        print("\nThen run:")
        print("   python test/setup_firebase_database.py")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
