import { NavLink } from "react-router-dom";
import { LayoutDashboard, Globe, Send, History, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import clsx from "clsx";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Дашборд" },
  { to: "/domains", icon: Globe, label: "Домены и ящики" },
  { to: "/campaigns/new", icon: Send, label: "Новая рассылка" },
  { to: "/campaigns", icon: History, label: "Кампании" },
];

export default function Sidebar() {
  const { logout, user } = useAuth();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-6">
        <Send className="h-6 w-6 text-primary-600" />
        <span className="text-lg font-bold text-gray-900">Email Service</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                isActive
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-gray-200 p-4">
        <div className="mb-2 text-sm text-gray-500 truncate">{user?.username}</div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <LogOut className="h-4 w-4" />
          Выйти
        </button>
      </div>
    </aside>
  );
}
