/**
 * Firestore Wrapper with Automatic Collection Prefixing
 *
 * This wrapper transparently handles collection prefixing for multi-project
 * Firebase databases. Developers use normal Firestore APIs without worrying
 * about prefixes.
 *
 * Usage:
 *   import { db } from '@/lib/firestore';
 *   import { collection, addDoc, getDocs } from '@/lib/firestore';
 *
 *   // Just use it normally - prefixing is automatic!
 *   const docRef = await addDoc(collection(db, 'users'), { name: 'John' });
 *   const snapshot = await getDocs(collection(db, 'users'));
 */

import {
  getFirestore,
  collection as firestoreCollection,
  doc as firestoreDoc,
  collectionGroup as firestoreCollectionGroup,
  type Firestore,
  type CollectionReference,
  type DocumentReference,
  type Query
} from 'firebase/firestore';

// Re-export all Firestore functions that don't need wrapping
export {
  // Document operations
  getDoc,
  getDocs,
  addDoc,
  setDoc,
  updateDoc,
  deleteDoc,
  onSnapshot,

  // Query operations
  query,
  where,
  orderBy,
  limit,
  startAt,
  startAfter,
  endAt,
  endBefore,
  limitToLast,

  // Batch operations
  writeBatch,

  // Transactions
  runTransaction,

  // Timestamps
  serverTimestamp,
  Timestamp,

  // Types
  type QuerySnapshot,
  type DocumentSnapshot,
  type QueryDocumentSnapshot,
  type FieldValue,
  type WhereFilterOp,
  type OrderByDirection,
} from 'firebase/firestore';

// Get project ID from environment
const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || '';

/**
 * Add project prefix to collection name
 * @internal
 */
function addPrefix(collectionName: string): string {
  if (!PROJECT_ID) {
    // No project ID = no prefix (standalone Firebase project)
    return collectionName;
  }

  // If already prefixed, don't add again
  if (collectionName.startsWith(`proj_${PROJECT_ID}_`)) {
    return collectionName;
  }

  return `proj_${PROJECT_ID}_${collectionName}`;
}

/**
 * Remove project prefix from collection name
 * @internal
 */
function removePrefix(prefixedName: string): string {
  if (!PROJECT_ID) {
    return prefixedName;
  }

  const prefix = `proj_${PROJECT_ID}_`;
  if (prefixedName.startsWith(prefix)) {
    return prefixedName.slice(prefix.length);
  }

  return prefixedName;
}

/**
 * Wrapped collection() that automatically adds prefix
 *
 * @example
 * // Instead of: collection(db, 'proj_1_abc_users')
 * // Just use: collection(db, 'users')
 * const usersRef = collection(db, 'users');
 */
export function collection(
  firestore: Firestore,
  collectionName: string,
  ...pathSegments: string[]
): CollectionReference {
  // Handle subcollections: collection(db, 'users', 'userId', 'orders')
  if (pathSegments.length > 0) {
    // Add prefix only to collection names (odd indices in path)
    const fullPath = [collectionName, ...pathSegments];
    const prefixedPath = fullPath.map((segment, index) => {
      // Collection names are at even indices: 0, 2, 4...
      if (index % 2 === 0) {
        return addPrefix(segment);
      }
      return segment;
    });

    return firestoreCollection(firestore, prefixedPath[0], ...prefixedPath.slice(1));
  }

  // Simple collection
  return firestoreCollection(firestore, addPrefix(collectionName));
}

/**
 * Wrapped doc() that automatically adds prefix to collection names
 *
 * @example
 * // Instead of: doc(db, 'proj_1_abc_users', 'userId')
 * // Just use: doc(db, 'users', 'userId')
 * const userRef = doc(db, 'users', 'userId');
 */
export function doc(
  firestore: Firestore,
  collectionName: string,
  ...pathSegments: string[]
): DocumentReference {
  // Handle document paths: doc(db, 'users', 'userId', 'orders', 'orderId')
  const fullPath = [collectionName, ...pathSegments];
  const prefixedPath = fullPath.map((segment, index) => {
    // Collection names are at even indices: 0, 2, 4...
    if (index % 2 === 0) {
      return addPrefix(segment);
    }
    return segment;
  });

  return firestoreDoc(firestore, prefixedPath[0], ...prefixedPath.slice(1));
}

/**
 * WARNING: collectionGroup() queries ALL projects!
 *
 * Collection groups bypass prefixing and query across ALL projects
 * in the shared database. Use with caution.
 *
 * If you need to query a specific collection group, use the prefixed name:
 * collectionGroup(db, 'proj_1_abc_orders')
 */
export function collectionGroup(
  firestore: Firestore,
  collectionId: string
): Query {
  console.warn(
    `collectionGroup('${collectionId}') queries across ALL projects. ` +
    `Use collectionGroup('${addPrefix(collectionId)}') to query only this project.`
  );
  return firestoreCollectionGroup(firestore, collectionId);
}

/**
 * Initialize and export Firestore database instance
 * This should be imported from '@/lib/firestore', not '@/lib/firebase'
 */
import { app } from '@/lib/firebase';
export const db: Firestore = getFirestore(app);

/**
 * Utility: Get the prefixed collection name (for debugging)
 */
export function getPrefixedName(collectionName: string): string {
  return addPrefix(collectionName);
}

/**
 * Utility: Get the original collection name (for debugging)
 */
export function getOriginalName(prefixedName: string): string {
  return removePrefix(prefixedName);
}

/**
 * Utility: Get current project ID
 */
export function getProjectId(): string {
  return PROJECT_ID;
}
