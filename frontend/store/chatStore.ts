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
            console.log("sendQuery", query);
            const res = await api.post(
                "chats/chat/multiline",
                {},
                {
                    params: {query: query},
                    headers: {
                        ...api.defaults.headers.common,
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            console.log("res==", res);
            set({answer: res.data.summary || "No answer", loading: false});
        } catch (err: any) {
            console.log("err==", err);
            set({
                error: err.response?.data?.error || "Something went wrong",
                loading: false,
            });
        }
    },

    clear: () => set({answer: "", error: null}),
}));