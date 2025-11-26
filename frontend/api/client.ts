import axios, {AxiosRequestConfig} from "axios";
import {useAuthStore} from "@/store/authStore";


const api = axios.create({
    baseURL: 'http://localhost:8001/api/v1',
    headers: {
        'Content-Type': 'application/json'
    },
    withCredentials: true,
});

// api.interceptors.request.use((config) => {
//     const publicPaths = ['/users/login', '/users/register'];
//     const isPublicPath = publicPaths.some(path => config.url?.includes(path));
//
//     if (!isPublicPath) {
//         const token = useAuthStore.getState().token;
//         if (token) {
//             config.headers.Authorization = `Bearer ${token}`;
//         }
//     }
//     return config;
// });

export default api;