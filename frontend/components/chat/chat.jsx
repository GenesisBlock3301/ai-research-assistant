'use client';

import React, {useState, useEffect, useCallback} from "react";
import {useChatStore} from "@/store/chatStore";

const Chat = () => {
    const [query, setQuery] = useState("");

    const {answer, loading, error, sendQuery, clear} = useChatStore();
    useEffect(() => {
        if (query === "") clear();
    }, [query, clear]);

    const handleSend = useCallback(() => {
        if (!query.trim() || loading) return;
        console.log("Sending query", query.trim());
        sendQuery(query.trim());
        setQuery("");
    }, [query, loading, sendQuery]);

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Input + Send Button */}
            <div className="flex gap-2">
                <input
                    type="text"
                    placeholder="Ask anything about your documents..."
                    className="flex-1 p-3 border rounded-lg bg-blue-950 text-white placeholder-gray-400
                     focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                />

                <button
                    onClick={handleSend}
                    disabled={loading || !query.trim()}
                    className={`px-6 py-3 rounded-lg font-medium text-white transition ${
                        loading || !query.trim()
                            ? "bg-blue-400 cursor-not-allowed"
                            : "bg-blue-600 hover:bg-blue-700 shadow-md"
                    }`}
                >
                    {loading ? "Thinking..." : "Send"}
                </button>
            </div>

            {/* Response Box */}
            <div className="mt-6 p-6 border rounded-lg bg-blue-950 text-white min-h-64 overflow-auto">
                {loading && (
                    <div className="flex justify-center items-center h-full">
                        <div className="w-12 h-12 border-4 border-white border-dashed rounded-full animate-spin"></div>
                    </div>
                )}

                {!loading && error && (
                    <div className="text-red-400">
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {!loading && !error && answer && (
                    <div className="whitespace-pre-wrap">{answer}</div>
                )}

                {!loading && !error && !answer && (
                    <div className="text-gray-400 italic">
                        Here your response will appear...
                    </div>
                )}
            </div>
        </>
    );
};

export default Chat;
