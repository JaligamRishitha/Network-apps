import { NavLink, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  HeartIcon,
  MegaphoneIcon,
  ShoppingCartIcon,
  Squares2X2Icon,
  UserCircleIcon,
  CogIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  BuildingOfficeIcon as BuildingOfficeIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  HeartIcon as HeartIconSolid,
  MegaphoneIcon as MegaphoneIconSolid,
  ShoppingCartIcon as ShoppingCartIconSolid,
  Squares2X2Icon as Squares2X2IconSolid,
  UserCircleIcon as UserCircleIconSolid,
  CogIcon as CogIconSolid,
  MagnifyingGlassIcon as MagnifyingGlassIconSolid,
} from '@heroicons/react/24/solid';

const navItems = [
  { path: '/home', label: 'Home', Icon: HomeIcon, IconSolid: HomeIconSolid },
  { path: '/contacts', label: 'Contacts', Icon: UserGroupIcon, IconSolid: UserGroupIconSolid },
  { path: '/accounts', label: 'Accounts', Icon: BuildingOfficeIcon, IconSolid: BuildingOfficeIconSolid },
  { path: '/sales', label: 'Sales', Icon: ChartBarIcon, IconSolid: ChartBarIconSolid },
  { path: '/service', label: 'Service', Icon: HeartIcon, IconSolid: HeartIconSolid },
  { path: '/service-management', label: 'Service Mgmt', Icon: Squares2X2Icon, IconSolid: Squares2X2IconSolid },
  // { path: '/marketing', label: 'Marketing', Icon: MegaphoneIcon, IconSolid: MegaphoneIconSolid }, // Hidden
  // { path: '/commerce', label: 'Commerce', Icon: ShoppingCartIcon, IconSolid: ShoppingCartIconSolid }, // Hidden
  // { path: '/generative', label: 'Generative Canvas', Icon: Squares2X2Icon, IconSolid: Squares2X2IconSolid }, // Hidden
  { path: '/servicenow', label: 'ServiceNow', Icon: CogIcon, IconSolid: CogIconSolid },
  { path: '/servicenow-tracking', label: 'Tracking', Icon: MagnifyingGlassIcon, IconSolid: MagnifyingGlassIconSolid },
  { path: '/account', label: 'Your Account', Icon: UserCircleIcon, IconSolid: UserCircleIconSolid },
];

export default function LeftNav() {
  const location = useLocation();

  return (
    <nav className="fixed left-0 top-0 h-full w-[72px] bg-sf-nav flex flex-col items-center py-4 z-50">
      {navItems.map(({ path, label, Icon, IconSolid }) => {
        const isActive = location.pathname === path ||
          (path !== '/home' && location.pathname.startsWith(path));

        return (
          <NavLink
            key={path}
            to={path}
            className={`flex flex-col items-center justify-center w-full py-3 px-2 text-[10px] transition-colors ${
              isActive
                ? 'bg-sf-blue-700 text-white'
                : 'text-gray-300 hover:bg-sf-blue-800 hover:text-white'
            }`}
          >
            <div className={`p-1.5 rounded-md ${isActive ? 'bg-white/20' : ''}`}>
              {isActive ? (
                <IconSolid className="w-6 h-6" />
              ) : (
                <Icon className="w-6 h-6" />
              )}
            </div>
            <span className="mt-1 text-center leading-tight">{label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
