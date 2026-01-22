/**
 * Firestore Proxy Client
 *
 * This client provides a Firestore-like API that communicates with the backend proxy.
 * All operations are handled securely by the backend, keeping Firebase credentials safe.
 *
 * Usage:
 *   import { db } from '@/lib/firestore';
 *   import { addDoc, collection, getDocs } from '@/lib/firestore';
 *
 *   const docRef = await addDoc(collection(db, 'users'), { name: 'John' });
 *   const snapshot = await getDocs(collection(db, 'users'));
 */

// Types
export interface DocumentData {
  [field: string]: any;
}

export interface QueryDocumentSnapshot {
  id: string;
  data(): DocumentData;
  exists: boolean;
}

export interface QuerySnapshot {
  docs: QueryDocumentSnapshot[];
  size: number;
  empty: boolean;
}

export interface DocumentReference {
  id: string;
  path: string;
}

export interface CollectionReference {
  path: string;
  _collectionName: string;
}

// Firebase proxy configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || '';

/**
 * Mock Firestore instance
 * This is just a placeholder - actual operations go through the proxy
 */
export const db = {
  type: 'firestore-proxy',
  projectId: PROJECT_ID
};

/**
 * Create a collection reference
 */
export function collection(firestore: any, collectionName: string): CollectionReference {
  return {
    path: collectionName,
    _collectionName: collectionName
  };
}

/**
 * Add a document to a collection
 */
export async function addDoc(
  collectionRef: CollectionReference,
  data: DocumentData
): Promise<DocumentReference> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/add`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collection: collectionRef._collectionName,
          data
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add document');
    }

    const result = await response.json();
    return {
      id: result.id,
      path: `${collectionRef.path}/${result.id}`
    };
  } catch (error) {
    console.error('Error adding document:', error);
    throw error;
  }
}

/**
 * Set a document with a specific ID
 */
export async function setDoc(
  docRef: DocumentReference,
  data: DocumentData
): Promise<void> {
  try {
    // Extract collection name from path
    const pathParts = docRef.path.split('/');
    const collectionName = pathParts[0];

    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/add`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collection: collectionName,
          data,
          docId: docRef.id
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to set document');
    }
  } catch (error) {
    console.error('Error setting document:', error);
    throw error;
  }
}

/**
 * Get all documents from a collection
 */
export async function getDocs(
  collectionRef: CollectionReference
): Promise<QuerySnapshot> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/get?collection=${encodeURIComponent(collectionRef._collectionName)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get documents');
    }

    const result = await response.json();
    const docs: QueryDocumentSnapshot[] = result.documents.map((doc: any) => ({
      id: doc.id,
      data: () => doc.data,
      exists: true
    }));

    return {
      docs,
      size: docs.length,
      empty: docs.length === 0
    };
  } catch (error) {
    console.error('Error getting documents:', error);
    throw error;
  }
}

/**
 * Get a single document by ID
 */
export async function getDoc(
  docRef: DocumentReference
): Promise<QueryDocumentSnapshot> {
  try {
    // Extract collection name from path
    const pathParts = docRef.path.split('/');
    const collectionName = pathParts[0];

    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/get?collection=${encodeURIComponent(collectionName)}&doc_id=${encodeURIComponent(docRef.id)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return {
          id: docRef.id,
          data: () => ({}),
          exists: false
        };
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get document');
    }

    const result = await response.json();
    return {
      id: result.id,
      data: () => result.data,
      exists: true
    };
  } catch (error) {
    console.error('Error getting document:', error);
    throw error;
  }
}

/**
 * Update a document
 */
export async function updateDoc(
  docRef: DocumentReference,
  data: Partial<DocumentData>
): Promise<void> {
  try {
    // Extract collection name from path
    const pathParts = docRef.path.split('/');
    const collectionName = pathParts[0];

    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/update`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collection: collectionName,
          docId: docRef.id,
          data
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update document');
    }
  } catch (error) {
    console.error('Error updating document:', error);
    throw error;
  }
}

/**
 * Delete a document
 */
export async function deleteDoc(docRef: DocumentReference): Promise<void> {
  try {
    // Extract collection name from path
    const pathParts = docRef.path.split('/');
    const collectionName = pathParts[0];

    const response = await fetch(
      `${API_BASE_URL}/api/v1/firebase/projects/${PROJECT_ID}/firestore/delete?collection=${encodeURIComponent(collectionName)}&doc_id=${encodeURIComponent(docRef.id)}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete document');
    }
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
}

/**
 * Create a document reference
 */
export function doc(
  firestore: any,
  collectionName: string,
  docId: string
): DocumentReference {
  return {
    id: docId,
    path: `${collectionName}/${docId}`
  };
}

/**
 * Server timestamp placeholder
 */
export function serverTimestamp(): any {
  return new Date().toISOString();
}

/**
 * Timestamp class
 */
export class Timestamp {
  seconds: number;
  nanoseconds: number;

  constructor(seconds: number, nanoseconds: number) {
    this.seconds = seconds;
    this.nanoseconds = nanoseconds;
  }

  static now(): Timestamp {
    const now = Date.now();
    return new Timestamp(Math.floor(now / 1000), (now % 1000) * 1000000);
  }

  static fromDate(date: Date): Timestamp {
    const ms = date.getTime();
    return new Timestamp(Math.floor(ms / 1000), (ms % 1000) * 1000000);
  }

  toDate(): Date {
    return new Date(this.seconds * 1000 + this.nanoseconds / 1000000);
  }
}
