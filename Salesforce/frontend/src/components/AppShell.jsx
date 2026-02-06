import { Outlet } from 'react-router-dom';
import LeftNav from './LeftNav';
import TopBar from './TopBar';
import ToDoList from './ToDoList';

export default function AppShell() {
  return (
    <div className="min-h-screen bg-sf-bg">
      <LeftNav />
      <TopBar />
      <main className="ml-[72px] pt-14 min-h-screen">
        <Outlet />
      </main>
      <ToDoList />
    </div>
  );
}
