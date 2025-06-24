import React, { useState, useEffect } from 'react';
import { useEmails, useEmailStats } from '@/hooks/useEmails';
import { Email } from '@/types';
import { useMainCategories } from '@/hooks/useCategories';
import { useAuth } from '@/lib/auth.tsx';
import { useNotifications } from '@/hooks/useNotifications';
import EmailList from '@/components/EmailList';
import { useLocation } from 'wouter';
import { 
  Mail, 
  Inbox, 
  Send, 
  Archive, 
  Trash2, 
  Star, 
  Search, 
  Filter, 
  RefreshCw, 
  Settings, 
  LogOut, 
  Bell,
  CheckCircle,
  User,
  ChevronDown,
  Plus, 
  Users
} from 'lucide-react';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
} from '@/components/ui/pagination';

const Dashboard: React.FC = () => {
  const [, setLocation] = useLocation();
  const { user, logout } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const [accounts, setAccounts] = useState<{ email: string; active: boolean }[]>([]);

  // Fetch data
  const emailFilters = {
    folder: selectedCategory === 'all' ? 'inbox' : 
            selectedCategory === 'trash' ? 'trash' :
            selectedCategory === 'archived' ? 'archive' :
            selectedCategory === 'starred' ? 'starred' :
            selectedCategory === 'sent' ? 'sent' :
            selectedCategory === 'unread' ? 'unread' : 'inbox',
    account: selectedAccount === 'all' ? undefined : selectedAccount,
    search: searchQuery || undefined,
    page,
    per_page: perPage,
  };
  
  console.log('🔍 Dashboard - Email filters:', emailFilters);
  console.log('🔍 Dashboard - Selected category:', selectedCategory);
  console.log('🔍 Dashboard - Folder being sent:', emailFilters.folder);
  
  const { emails, loading, error, pagination, refetch, markAsRead, markAsUnread, performAction } = useEmails(emailFilters);

  const { stats, refetch: refetchStats } = useEmailStats();
  const { categories } = useMainCategories();
  const { notifications, markAllAsRead, markAsRead: markNotificationAsRead, refetch: refetchNotifications } = useNotifications();

  // Listen for stats refresh events and also refresh inbox/trash list
  useEffect(() => {
    const handleStatsRefresh = () => {
      console.log('🔄 Dashboard - Refreshing email stats and inbox/trash list...');
      refetchStats();
      refetch(); // Refresh the email list as well
    };

    window.addEventListener('refreshEmailStats', handleStatsRefresh);
    return () => {
      window.removeEventListener('refreshEmailStats', handleStatsRefresh);
    };
  }, [refetchStats, refetch]);

  // Debug stats
  useEffect(() => {
    console.log('📊 Dashboard - Current stats:', stats);
    console.log('📊 Dashboard - Current emails count:', emails.length);
  }, [stats, emails]);

  // Fetch accounts on mount and when emails change
  useEffect(() => {
    async function fetchAccounts() {
      try {
        const res = await import('@/lib/api').then(m => m.emailAPI.getAccounts());
        setAccounts(res);
      } catch (e) {
        setAccounts([]);
      }
    }
    fetchAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emails]);

  const handleLogout = () => {
    logout();
  };

  const handleSettingsClick = () => {
    setLocation('/settings');
  };

  const handleEmailClick = async (email: Email) => {
    // Mark as read in local database only when opening email
    if (!email.is_read) {
      await markAsRead(email.id);
      refetchStats(); // Refetch stats to update unread count
    }
    setSelectedEmail(email);
  };

  const systemUnreadCount = notifications?.filter(n => !n.is_read).length || 0;

  // Helper to get correct total for current category
  const getCategoryTotal = () => {
    if (!stats) return 0;
    
    // If a specific account is selected, use account-specific counts
    if (selectedAccount !== 'all' && stats.emails_by_account) {
      const accountCount = stats.emails_by_account[selectedAccount];
      if (accountCount !== undefined) {
        if (selectedCategory === 'all') return accountCount;
        if (selectedCategory === 'unread') {
          // For unread, we need to calculate from the current emails list
          return emails.filter(email => !email.is_read).length;
        }
        // For other categories, use pagination total as fallback
        return pagination.total;
      }
    }
    
    // Default behavior for "All Accounts"
    if (selectedCategory === 'all') return stats.total_emails || 0;
    if (selectedCategory === 'unread') return stats.unread_emails || 0;
    return stats.emails_by_category?.[selectedCategory] || pagination.total;
  };

  // Helper to get account-specific count for sidebar
  const getAccountSpecificCount = (category: string) => {
    if (!stats) return 0;
    
    if (selectedAccount === 'all') {
      // Show all accounts count
      if (category === 'all') return stats.total_emails || 0;
      if (category === 'unread') return stats.unread_emails || 0;
      return stats.emails_by_category?.[category] || 0;
    } else {
      // Show specific account count
      if (category === 'all') return stats.emails_by_account?.[selectedAccount] || 0;
      if (category === 'unread') {
        // For unread, calculate from current emails
        return emails.filter(email => !email.is_read).length;
      }
      // For other categories, show 0 as we don't have category breakdown by account
      return 0;
    }
  };

  // Notification icon click handler
  const handleNotificationClick = () => {
    setShowNotifications(!showNotifications);
    if (!showNotifications) {
      refetchNotifications(); // fetch latest notifications when opening
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Left Sidebar - Categories */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2 mb-4">
            <Mail className="h-6 w-6 text-blue-600" />
            <h1 className="text-lg font-semibold text-gray-900">Email Hub</h1>
          </div>
          
          {/* User Info */}
          <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.name || user?.email}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user?.email}
              </p>
            </div>
          </div>
          {/* Account Filter Dropdown */}
          <div className="mt-4">
            <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Accounts</label>
            <select
              value={selectedAccount}
              onChange={e => { setSelectedAccount(e.target.value); setPage(1); }}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-700 text-sm w-full"
            >
              <option value="all">All Accounts</option>
              {accounts.map(acc => (
                <option key={acc.email} value={acc.email}>{acc.email}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Quick Actions removed as per user request */}

        {/* Categories */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Categories
            </h3>
            
            {/* Default Categories */}
            <div className="space-y-1">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'all' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Inbox className="h-4 w-4" />
                <span className="flex-1">Inbox</span>
                <span className="text-xs text-gray-500">{getAccountSpecificCount('all')}</span>
              </button>
              
              <button
                onClick={() => setSelectedCategory('unread')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'unread' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Mail className="h-4 w-4" />
                <span className="flex-1">Unread</span>
                <span className="text-xs text-gray-500">{getAccountSpecificCount('unread')}</span>
              </button>
              
              <button
                onClick={() => setSelectedCategory('starred')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'starred' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Star className="h-4 w-4" />
                <span className="flex-1">Starred</span>
              </button>
              
              <button
                onClick={() => setSelectedCategory('sent')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'sent' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Send className="h-4 w-4" />
                <span className="flex-1">Sent</span>
              </button>
              
              <button
                onClick={() => setSelectedCategory('archived')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'archived' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Archive className="h-4 w-4" />
                <span className="flex-1">Archived</span>
              </button>
              
              <button
                onClick={() => setSelectedCategory('trash')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                  selectedCategory === 'trash' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Trash2 className="h-4 w-4" />
                <span className="flex-1">Trash</span>
              </button>
            </div>

            {/* Dynamic Categories */}
            {categories && categories.length > 0 && (
              <div className="mt-6">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Custom Categories
                </h3>
                <div className="space-y-1">
                  {categories.map((category) => (
                    <button
                      key={category.main_category}
                      onClick={() => setSelectedCategory(category.main_category)}
                      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-50 ${
                        selectedCategory === category.main_category ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                      }`}
                    >
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="flex-1">{category.main_category}</span>
                      <span className="text-xs text-gray-500">{category.count}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        {/* Settings & Logout at bottom */}
        <div className="mt-auto p-4 border-t border-gray-200">
          <button
            onClick={handleSettingsClick}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
          <button
            onClick={handleLogout}
            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2 text-red-600"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content Area - FIXED STRUCTURE & RESPONSIVE */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar - Always visible, responsive */}
        <div className="bg-white border-b border-gray-200 py-2 px-4 flex items-center gap-2 w-full overflow-x-hidden">
          {/* Search bar - fully left, wide */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search emails..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full"
            />
          </div>
          {/* Icons: refresh, filter */}
          <button className="p-2 hover:bg-gray-100 rounded-lg ml-6" onClick={() => refetch()} aria-label="Refresh emails">
            <RefreshCw className="h-4 w-4 text-gray-500" />
          </button>
          {/* <button className="p-2 hover:bg-gray-100 rounded-lg">
            <Filter className="h-4 w-4 text-gray-500" />
          </button> */}
          {/* Notification icon - rightmost */}
          <div className="relative ml-4">
            <button
              onClick={handleNotificationClick}
              className="p-2 hover:bg-gray-100 rounded-lg relative"
            >
              <Bell className="h-4 w-4 text-gray-500" />
              {(stats?.unread_emails ?? 0) > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center px-1">
                  {(stats?.unread_emails ?? 0) > 9 ? '10+' : stats?.unread_emails}
                </span>
              )}
            </button>
            {showNotifications && (
              <div className="fixed top-14 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Notifications</h3>
                    <button
                      onClick={markAllAsRead}
                      className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                    >
                      <CheckCircle className="h-3 w-3" />
                      <span>Mark all read</span>
                    </button>
                  </div>
                </div>
                {/* Unread Emails Section */}
                <div className="border-b border-gray-200">
                  <div className="p-3 pb-0">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Unread Emails</h4>
                    {emails.filter(e => !e.is_read).length === 0 ? (
                      <div className="text-gray-400 text-sm py-2">No unread emails</div>
                    ) : (
                      emails.filter(e => !e.is_read).slice(0, 5).map(email => (
                        <div
                          key={email.id}
                          className="p-2 rounded hover:bg-blue-50 cursor-pointer flex flex-col border-b last:border-b-0"
                          onClick={() => handleEmailClick(email)}
                        >
                          <span className="font-medium text-gray-900 text-sm truncate">{email.subject || '(No Subject)'}</span>
                          <span className="text-xs text-gray-500 truncate">{email.sender}</span>
                          <span className="text-xs text-gray-400">{new Date(email.date).toLocaleString()}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                {/* System Notifications Section */}
                <div className="max-h-64 overflow-y-auto">
                  {notifications && notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-3 border-b border-gray-100 hover:bg-gray-50 ${
                          !notification.is_read ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => markNotificationAsRead(notification.id)}
                      >
                        <div className="flex items-start space-x-3">
                          <div className={`w-2 h-2 rounded-full mt-2 ${
                            notification.type === 'error' ? 'bg-red-500' :
                            notification.type === 'warning' ? 'bg-yellow-500' :
                            notification.type === 'success' ? 'bg-green-500' :
                            'bg-blue-500'
                          }`}></div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              {new Date(notification.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-gray-500">
                      No notifications
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          {/* Pagination - right aligned */}
          <div className="flex items-center space-x-2 text-sm text-gray-600 ml-auto">
            <span>
              {((page - 1) * perPage + 1)} – {Math.min(page * perPage, getCategoryTotal())} of {getCategoryTotal()}
            </span>
            <button
              onClick={() => page > 1 && setPage(page - 1)}
              disabled={page === 1}
              className={`p-2 rounded hover:bg-gray-100 ${page === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-label="Previous page"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" /></svg>
            </button>
            <button
              onClick={() => page < pagination.pages && setPage(page + 1)}
              disabled={page === pagination.pages}
              className={`p-2 rounded hover:bg-gray-100 ${page === pagination.pages ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-label="Next page"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
          
        </div>
        {/* Email List with Scroll and Pagination */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Main content */}
          <main className="flex-1 overflow-y-auto">
            <div className="p-4">
              {/* Email List */}
              <div className="flex-1 overflow-y-auto bg-white p-2">
                {loading ? (
                  <div className="text-center p-8 text-gray-500">Loading emails...</div>
                ) : error ? (
                  <div className="text-center p-8 text-red-500">{error}</div>
                ) : (
                  <div className="bg-white rounded-lg shadow-md">
                    <EmailList emails={emails} onEmailClick={handleEmailClick} markAsUnread={markAsUnread} performAction={performAction} />
                  </div>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
