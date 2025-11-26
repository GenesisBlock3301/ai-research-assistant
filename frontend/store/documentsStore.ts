import {create} from "zustand";
import api from "@/api/client";
import {useAuthStore} from "@/store/authStore";

interface Document {
    id: string;
    title: string;
    createdAt?: string;
    updatedAt?: string;
}

interface DocumentState {
    documents: Document[];
    loading: boolean;
    error: string | null;
    hydrated: boolean;
    setHydrated: (hydrate: boolean) => void;

    //  action
    fetchDocuments: () => Promise<void>;
    // uploadingDocuments: (file: File, title?: string) => Promise<Document[]>;
    // deleteDocument: (id: number) => Promise<void>;
    // addDocument: (doc: Document) => void;        // for optimistic updates
    // removeDocument: (id: number) => void;        // for optimistic updates
    // clearError: () => void;
    // reset: () => void;                           // important: clear on logout
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
    documents: [],
    loading: false,
    error: null,
    hydrated: false,
    setHydrated: (value) => set({hydrated: value}),
    fetchDocuments: async () => {
        set({loading: true, error: null})
        try {
            const token = useAuthStore.getState().token;
            const res = await api.get(
                "documents/list/",
                {
                    headers: {
                        ...api.defaults.headers.common,
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            const docs: Document[] = res.data ?? [];
            set({documents: docs})
        } catch (e) {
            console.error(e);
        } finally {
            set({loading: false})
        }
    },
}))