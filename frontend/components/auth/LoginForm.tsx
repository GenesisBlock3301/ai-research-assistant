import React, {useState} from 'react'


interface LoginFormProps {
    onSubmit: (email: string, password: string) => void;
    loading: boolean;
}

const LoginForm = ({onSubmit, loading}: LoginFormProps) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    return (
        <form
            onSubmit={(e) => {
                e.preventDefault();
                onSubmit(email, password);
            }}
            className="bg-white p-8 rounded shadow-md w-96 flex flex-col space-y-4"
        >
            <h2 className="text-xl font-bold text-center text-black">Login</h2>
            <input
                type="email"
                placeholder="Email"
                name="email"
                className="p-2 border rounded placeholder-gray-400 text-black"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
            />
            <input
                type="password"
                placeholder="Password"
                name="password"
                className="p-2 border rounded placeholder-gray-700 text-black"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button
                type="submit"
                className="bg-green-600 py-2 rounded hover:bg-green-700 text-black"
                disabled={loading}
            >
                {loading ? "Loading..." : "Login"}
            </button>
        </form>
    )
}
export default LoginForm;
