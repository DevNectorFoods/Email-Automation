import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Link, useLocation } from "wouter";
import { 
  Mail, 
  Gauge, 
  Inbox, 
  Bot, 
  Layers, 
  Users, 
  Trash2, 
  Bell, 
  Settings,
  LogOut,
  Crown,
  Server
} from "lucide-react";

interface SidebarProps {
  user: {
    id: number;
    name: string;
    email: string;
    role: string;
  };
  onLogout: () => void;
}

export default function Sidebar({ user, onLogout }: SidebarProps) {
  const [location] = useLocation();
  
  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'super_admin':
        return (
          <Badge className="bg-blue-100 text-blue-800">
            <Crown className="mr-1 w-3 h-3" />
            All Access
          </Badge>
        );
      case 'admin':
        return <Badge variant="secondary">Admin</Badge>;
      default:
        return <Badge variant="outline">User</Badge>;
    }
  };

  const getRoleTitle = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'Super Admin';
      case 'admin':
        return 'Admin';
      default:
        return 'User';
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo and Brand */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Mail className="text-white w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-neutral-800">EmailFlow</h1>
            <p className="text-xs text-gray-500">AI Email Management</p>
          </div>
        </div>
      </div>

      {/* User Role Badge */}
      <div className="px-6 py-3 bg-blue-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-blue-800">{getRoleTitle(user.role)}</span>
          {getRoleBadge(user.role)}
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4 space-y-2">
        <Link href="/">
          <Button variant="ghost" className={`w-full justify-start ${location === '/' ? 'bg-blue-50 text-primary' : ''} hover:bg-blue-100`}>
            <Gauge className="mr-3 w-4 h-4" />
            Dashboard
          </Button>
        </Link>
        
        <Button variant="ghost" className="w-full justify-start">
          <Inbox className="mr-3 w-4 h-4" />
          All Emails
          <Badge className="ml-auto bg-red-100 text-red-800 text-xs">42</Badge>
        </Button>
        
        <Button variant="ghost" className="w-full justify-start">
          <Bot className="mr-3 w-4 h-4" />
          AI Categories
          <Badge className="ml-auto bg-accent text-white text-xs">AI</Badge>
        </Button>
        
        <Button variant="ghost" className="w-full justify-start">
          <Layers className="mr-3 w-4 h-4" />
          Draft Approvals
          <Badge className="ml-auto bg-amber-100 text-amber-800 text-xs">7</Badge>
        </Button>
        
        {(user.role === 'admin' || user.role === 'super_admin') && (
          <>
            <Link href="/email-accounts">
              <Button variant="ghost" className={`w-full justify-start ${location === '/email-accounts' ? 'bg-blue-50 text-primary' : ''} hover:bg-blue-100`}>
                <Server className="mr-3 w-4 h-4" />
                Email Accounts
              </Button>
            </Link>
            
            <Link href="/user-management">
              <Button variant="ghost" className={`w-full justify-start ${location === '/user-management' ? 'bg-blue-50 text-primary' : ''} hover:bg-blue-100`}>
              <Users className="mr-3 w-4 h-4" />
              User Management
            </Button>
            </Link>
          </>
        )}
        
        {user.role === 'super_admin' && (
          <Button variant="ghost" className="w-full justify-start">
            <Trash2 className="mr-3 w-4 h-4" />
            Deleted Mails
          </Button>
        )}
        
        <Button variant="ghost" className="w-full justify-start">
          <Bell className="mr-3 w-4 h-4" />
          Notifications
          <Badge className="ml-auto bg-red-500 text-white text-xs">3</Badge>
        </Button>
      </nav>

      {/* Account Info */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3 mb-3">
          <Avatar className="w-10 h-10">
            <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              {user.name.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
          <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-600">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="w-full" 
          onClick={onLogout}
        >
          <LogOut className="mr-2 w-4 h-4" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}
