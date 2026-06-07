import { useState } from 'react';
import { createUser } from '../api';

export default function UserPanel({ users, selectedUser, onSelectUser, onUserCreated }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!username.trim() || !email.trim()) return;

    setLoading(true);
    setError('');
    try {
      const newUser = await createUser(username.trim(), email.trim());
      setUsername('');
      setEmail('');
      onUserCreated(newUser);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-panel">
      <h2>👤 用户管理</h2>

      <form className="user-form" onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="email"
          placeholder="邮箱"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? '创建中...' : '新建用户'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="user-list">
        <h3>已有用户</h3>
        {users.length === 0 ? (
          <p className="muted">暂无用户，请先创建一个</p>
        ) : (
          <ul>
            {users.map((u) => (
              <li
                key={u.id}
                className={selectedUser?.id === u.id ? 'active' : ''}
                onClick={() => onSelectUser(u)}
              >
                <span className="user-name">{u.username}</span>
                <span className="user-email">{u.email}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
