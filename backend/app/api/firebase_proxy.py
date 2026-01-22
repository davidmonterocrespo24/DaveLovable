"""
Firebase Proxy Endpoints

This module provides proxy endpoints for Firebase operations, keeping credentials secure
on the backend while allowing generated projects to use Firebase functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import json

from app.db.session import get_db

router = APIRouter()

# Initialize Firebase Admin SDK
_firebase_app = None

def get_firebase_app():
    """Initialize Firebase Admin SDK with service account credentials"""
    global _firebase_app

    if _firebase_app is None:
        # Path to service account key
        cred_path = Path(__file__).parent.parent.parent / "dlovable-firebase-adminsdk-fbsvc-33ee906aab.json"

        if not cred_path.exists():
            raise FileNotFoundError(f"Firebase service account key not found at {cred_path}")

        cred = credentials.Certificate(str(cred_path))
        _firebase_app = firebase_admin.initialize_app(cred)

    return _firebase_app

def get_firestore_client():
    """Get Firestore client instance"""
    get_firebase_app()  # Ensure initialized
    return firestore.client()


@router.post("/projects/{project_id}/firestore/add")
async def add_document(
    project_id: int,
    request_body: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Add a document to Firestore with automatic collection prefixing

    Expected body:
    {
        "collection": "users",
        "data": { "name": "John", "email": "john@example.com" },
        "docId": "optional-custom-id"
    }
    """
    try:
        collection_name = request_body.get("collection")
        data = request_body.get("data")
        doc_id = request_body.get("docId")

        if not collection_name or not data:
            raise HTTPException(status_code=400, detail="Missing collection or data")

        # Get project unique ID from .firebase-state.json
        from app.services.filesystem_service import FileSystemService
        project_dir = FileSystemService.get_project_directory(project_id)
        firebase_state_path = project_dir / ".firebase-state.json"

        if not firebase_state_path.exists():
            raise HTTPException(status_code=404, detail="Firebase not activated for this project")

        with open(firebase_state_path, 'r', encoding='utf-8') as f:
            firebase_state = json.load(f)

        collection_prefix = firebase_state.get("collection_prefix", f"proj_{project_id}_")
        prefixed_collection = f"{collection_prefix}{collection_name}"

        # Add document to Firestore
        fs_client = get_firestore_client()

        if doc_id:
            doc_ref = fs_client.collection(prefixed_collection).document(doc_id)
            doc_ref.set(data)
            return {
                "success": True,
                "id": doc_id,
                "collection": collection_name,
                "prefixed_collection": prefixed_collection
            }
        else:
            doc_ref = fs_client.collection(prefixed_collection).add(data)
            # doc_ref is a tuple (timestamp, DocumentReference)
            actual_doc_ref = doc_ref[1] if isinstance(doc_ref, tuple) else doc_ref
            return {
                "success": True,
                "id": actual_doc_ref.id,
                "collection": collection_name,
                "prefixed_collection": prefixed_collection
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")


@router.get("/projects/{project_id}/firestore/get")
async def get_documents(
    project_id: int,
    collection: str,
    doc_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Get documents from Firestore with automatic collection prefixing

    Query params:
    - collection: Collection name (e.g., "users")
    - doc_id: Optional document ID. If not provided, returns all documents
    """
    try:
        # Get collection prefix
        from app.services.filesystem_service import FileSystemService
        project_dir = FileSystemService.get_project_directory(project_id)
        firebase_state_path = project_dir / ".firebase-state.json"

        if not firebase_state_path.exists():
            raise HTTPException(status_code=404, detail="Firebase not activated for this project")

        with open(firebase_state_path, 'r', encoding='utf-8') as f:
            firebase_state = json.load(f)

        collection_prefix = firebase_state.get("collection_prefix", f"proj_{project_id}_")
        prefixed_collection = f"{collection_prefix}{collection}"

        fs_client = get_firestore_client()

        if doc_id:
            # Get single document
            doc_ref = fs_client.collection(prefixed_collection).document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                return {
                    "success": True,
                    "id": doc.id,
                    "data": doc.to_dict()
                }
            else:
                raise HTTPException(status_code=404, detail="Document not found")
        else:
            # Get all documents in collection
            docs = fs_client.collection(prefixed_collection).stream()
            documents = []

            for doc in docs:
                documents.append({
                    "id": doc.id,
                    "data": doc.to_dict()
                })

            return {
                "success": True,
                "collection": collection,
                "documents": documents
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting documents: {str(e)}")


@router.put("/projects/{project_id}/firestore/update")
async def update_document(
    project_id: int,
    request_body: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update a document in Firestore

    Expected body:
    {
        "collection": "users",
        "docId": "user123",
        "data": { "name": "John Updated" }
    }
    """
    try:
        collection_name = request_body.get("collection")
        doc_id = request_body.get("docId")
        data = request_body.get("data")

        if not collection_name or not doc_id or not data:
            raise HTTPException(status_code=400, detail="Missing collection, docId, or data")

        # Get collection prefix
        from app.services.filesystem_service import FileSystemService
        project_dir = FileSystemService.get_project_directory(project_id)
        firebase_state_path = project_dir / ".firebase-state.json"

        if not firebase_state_path.exists():
            raise HTTPException(status_code=404, detail="Firebase not activated for this project")

        with open(firebase_state_path, 'r', encoding='utf-8') as f:
            firebase_state = json.load(f)

        collection_prefix = firebase_state.get("collection_prefix", f"proj_{project_id}_")
        prefixed_collection = f"{collection_prefix}{collection_name}"

        # Update document
        fs_client = get_firestore_client()
        doc_ref = fs_client.collection(prefixed_collection).document(doc_id)
        doc_ref.update(data)

        return {
            "success": True,
            "id": doc_id,
            "collection": collection_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")


@router.delete("/projects/{project_id}/firestore/delete")
async def delete_document(
    project_id: int,
    collection: str,
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document from Firestore

    Query params:
    - collection: Collection name
    - doc_id: Document ID
    """
    try:
        # Get collection prefix
        from app.services.filesystem_service import FileSystemService
        project_dir = FileSystemService.get_project_directory(project_id)
        firebase_state_path = project_dir / ".firebase-state.json"

        if not firebase_state_path.exists():
            raise HTTPException(status_code=404, detail="Firebase not activated for this project")

        with open(firebase_state_path, 'r', encoding='utf-8') as f:
            firebase_state = json.load(f)

        collection_prefix = firebase_state.get("collection_prefix", f"proj_{project_id}_")
        prefixed_collection = f"{collection_prefix}{collection}"

        # Delete document
        fs_client = get_firestore_client()
        fs_client.collection(prefixed_collection).document(doc_id).delete()

        return {
            "success": True,
            "id": doc_id,
            "collection": collection
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.get("/projects/{project_id}/firestore/config")
async def get_firebase_config(project_id: int, db: Session = Depends(get_db)):
    """
    Get Firebase web configuration for the project
    Returns only the public web config (no sensitive credentials)
    """
    try:
        # Get project unique ID
        from app.services.filesystem_service import FileSystemService
        project_dir = FileSystemService.get_project_directory(project_id)
        firebase_state_path = project_dir / ".firebase-state.json"

        if not firebase_state_path.exists():
            raise HTTPException(status_code=404, detail="Firebase not activated for this project")

        with open(firebase_state_path, 'r', encoding='utf-8') as f:
            firebase_state = json.load(f)

        # Return public config (these are safe to expose in frontend)
        return {
            "project_id": "dlovable",
            "project_unique_id": firebase_state.get("project_unique_id"),
            "collection_prefix": firebase_state.get("collection_prefix"),
            "proxy_enabled": True,
            "proxy_base_url": f"/api/v1/firebase/projects/{project_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")
