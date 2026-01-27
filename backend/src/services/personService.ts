import { db, collection, addDoc, getDocs, deleteDoc, doc, query, orderBy } from '../lib/firestore';

export interface Person {
  id?: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  age: number;
  createdAt: number;
}

const COLLECTION_NAME = 'people';

export const personService = {
  async addPerson(person: Omit<Person, 'id' | 'createdAt'>): Promise<Person> {
    const newPerson = {
      ...person,
      createdAt: Date.now(),
    };
    const docRef = await addDoc(collection(db, COLLECTION_NAME), newPerson);
    return { id: docRef.id, ...newPerson };
  },

  async getPeople(): Promise<Person[]> {
    const q = query(collection(db, COLLECTION_NAME), orderBy('createdAt', 'desc'));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...(doc.data() as Omit<Person, 'id'>)
    }));
  },

  async deletePerson(id: string): Promise<void> {
    await deleteDoc(doc(db, COLLECTION_NAME, id));
  }
};
