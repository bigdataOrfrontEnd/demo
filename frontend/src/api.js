const BASE = '/api';

export async function createUser(username, email) {
  const res = await fetch(`${BASE}/users/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `创建用户失败 (${res.status})`);
  }
  return res.json();
}

export async function getUserWithTodos(userId) {
  const res = await fetch(`${BASE}/users/${userId}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `获取用户失败 (${res.status})`);
  }
  return res.json();
}

export async function createTodo(userId, title) {
  const res = await fetch(`${BASE}/users/${userId}/todos/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `创建待办失败 (${res.status})`);
  }
  return res.json();
}
