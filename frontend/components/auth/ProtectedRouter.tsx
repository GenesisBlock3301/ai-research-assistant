'use client';

import {useRouter} from "next/navigation";
import {useAuthStore} from "@/store/authStore";
import React, {useEffect, useState} from "react";
import api from "@/api/client";

const fetchCurrentUser = async (token: string) => {
    try {
        const response = await api.get("/users/me", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        console.log("user_me response", response.data);
        return response.data;
    } catch (error) {
        console.error("Failed to fetch current user:", error);
        throw error; // re-throw so caller can handle it
    }
};


export default function ProtectedRouter({children}: { children: React.ReactNode }) {
    const router = useRouter();
    const {token, logout, setUser} = useAuthStore();
    const [loading, setLoading] = useState<boolean>(true);
    useEffect(() => {
        const verifyToken = async () => {
            try {
                console.log("token", token)
                if (!token) {
                    router.replace("/login");
                    return;
                }
                const user = await fetchCurrentUser(token);
                console.log("fetch current user", user)
                if (user) {
                    setUser(user);
                }else {
                    logout();
                    router.replace("/login");
                }
            }catch (error) {
                console.error("Failed to fetch current user:", error);
                logout();
            }finally {
                setLoading(false);
            }
        };
        verifyToken();
    }, [token, router, logout, setUser]);

    if (loading){
        return (
            <div className="flex justify-center items-center h-screen text-gray-500">
                checking authentication...
            </div>
        )
    };

    return <>{children}</>;
}