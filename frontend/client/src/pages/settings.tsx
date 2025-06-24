import React, { useState } from 'react';
import { useEmailAccounts } from '@/hooks/useSettings';
import { useAuth } from '@/lib/auth.tsx';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { 
  Mail, 
  Plus, 
  Trash2, 
  TestTube, 
  Settings as SettingsIcon,
  User,
  Shield,
  Bell,
  Database,
  ArrowLeft,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useLocation } from 'wouter';
import UserManagement from './userManagement';

const Settings: React.FC = () => {
  const [, setLocation] = useLocation();
  const { user } = useAuth();
  
  // Check if user is admin
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  
  const { 
    accounts, 
    loading, 
    error, 
    addAccount, 
    deleteAccount, 
    testAccount, 
    testAllAccounts,
    updateAccount 
  } = useEmailAccounts();

  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showTestResults, setShowTestResults] = useState(false);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [testing, setTesting] = useState(false);

  // Form state for adding new account
  const [newAccount, setNewAccount] = useState({
    email: '',
    password: '',
    imap_server: 'imap.hostinger.com',
    imap_port: 993
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const [activeSection, setActiveSection] = useState<'accounts' | 'profile' | 'system' | 'users'>('accounts');

  const handleAddAccount = async () => {
    // Validate form
    const errors: Record<string, string> = {};
    if (!newAccount.email) errors.email = 'Email is required';
    if (!newAccount.password) errors.password = 'Password is required';
    if (!newAccount.imap_server) errors.imap_server = 'IMAP server is required';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      await addAccount(newAccount);
      setShowAddDialog(false);
      setNewAccount({
        email: '',
        password: '',
        imap_server: 'imap.hostinger.com',
        imap_port: 993
      });
      setFormErrors({});
    } catch (error) {
      console.error('Failed to add account:', error);
    }
  };

  const handleTestAllAccounts = async () => {
    setTesting(true);
    try {
      const results = await testAllAccounts();
      setTestResults(results.results || []);
      setShowTestResults(true);
    } catch (error) {
      console.error('Failed to test accounts:', error);
    } finally {
      setTesting(false);
    }
  };

  const handleTestAccount = async (email: string) => {
    try {
      await testAccount(email);
      // You could show a toast notification here
    } catch (error) {
      console.error('Failed to test account:', error);
    }
  };

  const handleDeleteAccount = async (email: string) => {
    if (window.confirm(`Are you sure you want to delete ${email}?`)) {
      try {
        await deleteAccount(email);
      } catch (error) {
        console.error('Failed to delete account:', error);
      }
    }
  };

  const handleToggleAccountStatus = async (email: string, currentStatus: boolean) => {
    try {
      await updateAccount(email, { active: !currentStatus });
    } catch (error) {
      console.error('Failed to toggle account status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'connected':
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'error':
      case 'inactive':
        return 'bg-red-100 text-red-800';
      case 'testing':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setLocation('/')}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </button>
              <div className="flex items-center space-x-2">
                <SettingsIcon className="h-6 w-6 text-blue-600" />
                <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user?.email}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Navigation */}
          <div className="lg:col-span-1">
            <Card className="p-4 sticky top-24">
              <nav className="flex flex-col space-y-1">
                          <button
                  onClick={() => setActiveSection('accounts')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeSection === 'accounts'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Mail className="mr-3 h-5 w-5" />
                  <span>Email Accounts</span>
              </button>
              <button
                onClick={() => setActiveSection('profile')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeSection === 'profile'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
              >
                  <User className="mr-3 h-5 w-5" />
                  <span>User Profile</span>
              </button>
              <button
                onClick={() => setActiveSection('system')}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeSection === 'system'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
              >
                  <Database className="mr-3 h-5 w-5" />
                  <span>System Info</span>
              </button>
              {isAdmin && (
                <button
                  onClick={() => setActiveSection('users')}
                    className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeSection === 'users'
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                >
                    <Shield className="mr-3 h-5 w-5" />
                    <span>User Management</span>
                </button>
              )}
              </nav>
            </Card>
            </div>
          
          {/* Content */}
          <div className="lg:col-span-3">
            {activeSection === 'accounts' && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <CardTitle>Email Accounts</CardTitle>
                      {!isAdmin && (
                        <Badge variant="secondary" className="ml-2">
                          Admin Only
                        </Badge>
                      )}
                    </div>
                    {isAdmin && (
                      <div className="flex items-center space-x-2">
                        <Button
                          onClick={handleTestAllAccounts}
                          disabled={testing || loading}
                          variant="outline"
                          size="sm"
                        >
                          <TestTube className="h-4 w-4 mr-2" />
                          {testing ? 'Testing...' : 'Test All'}
                        </Button>
                        <Button
                          onClick={() => setShowAddDialog(true)}
                          size="sm"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Add Account
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {!isAdmin ? (
                    <div className="text-center py-8">
                      <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Admin access required</p>
                      <p className="text-sm text-gray-400 mt-1">
                        Only administrators can manage email accounts
                      </p>
                    </div>
                  ) : loading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="mt-2 text-gray-500">Loading accounts...</p>
                    </div>
                  ) : error ? (
                    <div className="text-center py-8">
                      <p className="text-red-600">Error loading accounts: {error}</p>
                      <Button onClick={() => window.location.reload()} className="mt-2">
                        Retry
                      </Button>
                    </div>
                  ) : accounts && accounts.length > 0 ? (
                    <div className="space-y-4">
                      {accounts.map((account: any) => (
                        <div key={account.email} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                <Mail className="h-5 w-5 text-blue-600" />
                              </div>
                              <div>
                                <h3 className="font-medium text-gray-900">{account.email}</h3>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleToggleAccountStatus(account.email, account.active)}
                              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors flex items-center space-x-1 ${
                                account.active 
                                  ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                                  : 'bg-red-100 text-red-800 hover:bg-red-200'
                              }`}
                            >
                              {account.active ? (
                                <>
                                  <CheckCircle className="h-3 w-3" />
                                  <span>Active</span>
                                </>
                              ) : (
                                <>
                                  <XCircle className="h-3 w-3" />
                                  <span>Inactive</span>
                                </>
                              )}
                            </button>
                            <Button
                              onClick={() => handleTestAccount(account.email)}
                              variant="outline"
                              size="sm"
                            >
                              <TestTube className="h-4 w-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteAccount(account.email)}
                              variant="outline"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">No email accounts configured</p>
                      <p className="text-sm text-gray-400 mt-1">
                        Add your first email account to get started
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
            {activeSection === 'profile' && (
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <User className="h-5 w-5 text-blue-600" />
                    <CardTitle>User Profile</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Username</Label>
                      <p className="text-gray-900">{user?.name || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Email</Label>
                      <p className="text-gray-900">{user?.email}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Role</Label>
                      <Badge className="bg-blue-100 text-blue-800">
                        {user?.role || 'User'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {activeSection === 'system' && (
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Database className="h-5 w-5 text-blue-600" />
                    <CardTitle>System Info</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Version</span>
                      <span className="text-sm font-medium">1.0.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Status</span>
                      <Badge className="bg-green-100 text-green-800">Online</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Last Updated</span>
                      <span className="text-sm font-medium">
                        {new Date().toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {isAdmin && activeSection === 'users' && (
              <UserManagement />
            )}
          </div>
        </div>
      </div>

      {/* Add Account Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Email Account</DialogTitle>
            <DialogDescription>
              Please fill out the form to add a new email account.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={newAccount.email}
                onChange={(e) => setNewAccount({ ...newAccount, email: e.target.value })}
                placeholder="your@email.com"
                className={formErrors.email ? 'border-red-500' : ''}
              />
              {formErrors.email && (
                <p className="text-sm text-red-500 mt-1">{formErrors.email}</p>
              )}
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={newAccount.password}
                onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })}
                placeholder="Enter password"
                className={formErrors.password ? 'border-red-500' : ''}
              />
              {formErrors.password && (
                <p className="text-sm text-red-500 mt-1">{formErrors.password}</p>
              )}
            </div>
            <div>
              <Label htmlFor="imap_server">IMAP Server</Label>
              <Input
                id="imap_server"
                autoComplete="off"
                value={newAccount.imap_server}
                onChange={(e) => setNewAccount({ ...newAccount, imap_server: e.target.value })}
                placeholder="imap.hostinger.com"
                className={formErrors.imap_server ? 'border-red-500' : ''}
              />
              {formErrors.imap_server && (
                <p className="text-sm text-red-500 mt-1">{formErrors.imap_server}</p>
              )}
            </div>
            <div>
              <Label htmlFor="imap_port">IMAP Port</Label>
              <Input
                id="imap_port"
                type="number"
                autoComplete="off"
                value={newAccount.imap_port}
                onChange={(e) => setNewAccount({ ...newAccount, imap_port: parseInt(e.target.value) || 993 })}
                placeholder="993"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddAccount}>
                Add Account
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Test Results Dialog */}
      <Dialog open={showTestResults} onOpenChange={setShowTestResults}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Results</DialogTitle>
            <DialogDescription>
              Results of testing all email account connections.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {testResults.length > 0 ? (
              testResults.map((result: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium">{result.email}</p>
                    <p className="text-sm text-gray-500">{result.message}</p>
                  </div>
                  <Badge className={getStatusColor(result.status)}>
                    {result.status}
                  </Badge>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No test results available</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Settings; 