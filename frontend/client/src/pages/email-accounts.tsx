import { useEffect } from "react";
import { useAuth } from "@/lib/auth.tsx";
import { useLocation } from "wouter";
import Sidebar from "@/components/Sidebar";
import EmailAccountsView from "@/components/EmailAccountsView";

export default function EmailAccounts() {
  const { user, logout } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!user) {
      setLocation("/login");
    }
  }, [user, setLocation]);

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar user={user} onLogout={logout} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-neutral-800">Email Account Settings</h2>
              <span className="text-sm text-gray-500">Configure your Hostinger email accounts for automated syncing</span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6">
          <EmailAccountsView />
        </main>
      </div>
    </div>
  );
}