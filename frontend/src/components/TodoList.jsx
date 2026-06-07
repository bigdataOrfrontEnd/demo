import { useState } from 'react';
import { createTodo } from '../api';

export default function TodoList({ user, todos, onTodoAdded }) {
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    setError('');
    try {
      const newTodo = await createTodo(user.id, title.trim());
      setTitle('');
      onTodoAdded(newTodo);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const completed = todos.filter((t) => t.is_completed).length;
  const total = todos.length;

  return (
    <div className="todo-panel">
      <div className="todo-header">
        <h2>📋 {user.username} 的待办事项</h2>
        <span className="todo-stats">
          {completed}/{total} 已完成
        </span>
      </div>

      <form className="todo-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="添加新的待办事项..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          autoFocus
        />
        <button type="submit" disabled={loading}>
          {loading ? '...' : '＋'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <ul className="todo-list">
        {todos.length === 0 ? (
          <li className="empty">暂无待办事项，在上方添加一个吧</li>
        ) : (
          todos.map((todo) => (
            <li key={todo.id} className={todo.is_completed ? 'done' : ''}>
              <span className="todo-check">
                {todo.is_completed ? '✅' : '⬜'}
              </span>
              <span className="todo-title">{todo.title}</span>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
