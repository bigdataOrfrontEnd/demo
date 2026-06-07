import { useState } from 'react';
import UserPanel from './components/UserPanel';
import TodoList from './components/TodoList';
import { getUserWithTodos } from './api';
import './App.css';

export default function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSelectUser = async (user) => {
    setSelectedUser(user);
    setLoading(true);
    try {
      const data = await getUserWithTodos(user.id);
      setTodos(data.todos || []);
    } catch (err) {
      setTodos([]);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserCreated = (newUser) => {
    setUsers((prev) => [...prev, newUser]);
    // 自动选中新创建的用户
    setSelectedUser(newUser);
    setTodos(newUser.todos || []);
  };

  const handleTodoAdded = (newTodo) => {
    setTodos((prev) => [...prev, newTodo]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>✅ TODO 应用</h1>
      </header>

      <main className="app-main">
        <UserPanel
          users={users}
          selectedUser={selectedUser}
          onSelectUser={handleSelectUser}
          onUserCreated={handleUserCreated}
        />

        {selectedUser && (
          loading ? (
            <div className="todo-panel">
              <p className="loading">加载中...</p>
            </div>
          ) : (
            <TodoList
              user={selectedUser}
              todos={todos}
              onTodoAdded={handleTodoAdded}
            />
          )
        )}
      </main>
    </div>
  );
}
