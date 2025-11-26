'use client';

import React from "react";
import ProtectedRouter from "@/components/auth/ProtectedRouter";
import DocumentList from "@/components/documents/DocumentList";
import Chat from "@/components/chat/chat";

const ChatPage = () => {

    return (
        <ProtectedRouter>
            <div className="grid grid-cols-12 gap-4 p-4 min-h-screen bg-gray-50">
                <div className="col-span-12 md:col-span-8 flex flex-col gap-4 py-4">
                    <Chat/>
                </div>
                <div className="col-span-12 md:col-span-4 p-4 border rounded bg-blue-950 h-full">
                    <DocumentList/>
                </div>
            </div>
        </ProtectedRouter>
    );
};

export default ChatPage;
