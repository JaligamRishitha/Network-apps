import { useState } from 'react';
import { ListBulletIcon, XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon } from '@heroicons/react/24/solid';

export default function ToDoList() {
  const [isOpen, setIsOpen] = useState(false);
  const [todos, setTodos] = useState([
    { id: 1, text: 'Follow up with Acme Corp', completed: false },
    { id: 2, text: 'Send proposal to Tech Solutions', completed: true },
    { id: 3, text: 'Schedule demo call', completed: false },
  ]);
  const [newTodo, setNewTodo] = useState('');

  const toggleTodo = (id) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const addTodo = () => {
    if (newTodo.trim()) {
      setTodos([...todos, { id: Date.now(), text: newTodo, completed: false }]);
      setNewTodo('');
    }
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  return (
    <div className="fixed bottom-0 left-[72px] z-40">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 bg-white px-4 py-2 rounded-t-lg shadow-md border border-b-0 border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <ListBulletIcon className="w-5 h-5" />
        <span>To Do List</span>
        {todos.filter(t => !t.completed).length > 0 && (
          <span className="bg-sf-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {todos.filter(t => !t.completed).length}
          </span>
        )}
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="absolute bottom-full left-0 w-80 bg-white rounded-t-lg shadow-lg border border-gray-200 mb-0">
          <div className="p-3 border-b flex items-center justify-between">
            <h3 className="font-medium text-gray-900">To Do List</h3>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <div className="max-h-64 overflow-auto">
            {todos.map(todo => (
              <div
                key={todo.id}
                className="flex items-center px-3 py-2 hover:bg-gray-50 group"
              >
                <button
                  onClick={() => toggleTodo(todo.id)}
                  className={`w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center ${
                    todo.completed
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'border-gray-300'
                  }`}
                >
                  {todo.completed && <CheckCircleIcon className="w-4 h-4" />}
                </button>
                <span className={`flex-1 text-sm ${todo.completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>
                  {todo.text}
                </span>
                <button
                  onClick={() => deleteTodo(todo.id)}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="p-3 border-t flex items-center space-x-2">
            <input
              type="text"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTodo()}
              placeholder="Add a task..."
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-sf-blue-500"
            />
            <button
              onClick={addTodo}
              className="p-1.5 bg-sf-blue-500 text-white rounded-md hover:bg-sf-blue-600"
            >
              <PlusIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
