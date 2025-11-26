import {create} from "zustand";
import api from "@/api/client";
import {useAuthStore} from "@/store/authStore";

interface ChatState {
    loading: boolean;
    error: string | null;
    answer: string;

    sendQuery: (query: string) => Promise<void>;
    clear: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
    loading: false,
    error: null,
    answer: "",

    sendQuery: async (query: string) => {
        if (!query.trim()) return;

        set({loading: true, error: null, answer: ""});

        try {
            const token = useAuthStore.getState().token;
            const res = await api.post(
                "chats/chat/multiline",
                {query},
                {
                    headers: {
                        ...api.defaults.headers.common,
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            set({answer: res.data.summary || "No answer", loading: false});
        } catch (err: any) {
            set({
                error: err.response?.data?.error || "Something went wrong",
                loading: false,
            });
        }
    },

    clear: () => set({answer: "", error: null}),
}));