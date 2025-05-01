// src/features/auth/LoginPage.tsx
import React, { useState, ChangeEvent, JSX } from 'react';

export default function LoginPage(): JSX.Element {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleUsername = (e: ChangeEvent<HTMLInputElement>) => setUsername(e.target.value);
  const handlePassword = (e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value);

  return (
    <div className="p-4 max-w-sm mx-auto">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      <input
        className="block w-full mb-2 p-2 border rounded"
        value={username}
        onChange={handleUsername}
        placeholder="Username"
      />
      <input
        type="password"
        className="block w-full mb-4 p-2 border rounded"
        value={password}
        onChange={handlePassword}
        placeholder="Password"
      />
      <button className="px-4 py-2 bg-blue-600 text-white rounded">Login</button>
    </div>
  );
}