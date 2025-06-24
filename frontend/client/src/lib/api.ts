import { Email } from '@/types';

const API_BASE_URL = 'http://localhost:5000/api';

// Helper function to make API calls
async function apiCall(endpoint: string, options: RequestInit = {}): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

// Auth headers helper
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Authentication API
export const authAPI = {
  login: async (credentials: { email: string; password: string }) => {
    return apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  logout: async () => {
    return apiCall('/auth/logout', {
      method: 'POST',
    });
  },

  getProfile: async () => {
    return apiCall('/auth/profile');
  },

  updateProfile: async (profileData: { name?: string; email?: string }) => {
    return apiCall('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },

  validateToken: async () => {
    return apiCall('/auth/validate');
  },

  refreshToken: async () => {
    return apiCall('/auth/refresh', {
      method: 'POST',
    });
  },
};

// Email API
export const emailAPI = {
  // Get all emails with filtering and pagination
  getEmails: async (params: {
    page?: number;
    per_page?: number;
    category?: string;
    folder?: string;
    account?: string;
    search?: string;
    main_category?: string;
    sub_category?: string;
  } = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    return apiCall(`/emails/?${searchParams.toString()}`);
  },

  // Get email by ID
  getEmail: async (emailId: string) => {
    return apiCall(`/emails/${emailId}`);
  },

  // Mark email as read
  markAsRead: async (emailId: string) => {
    return apiCall(`/emails/${emailId}/read`, { method: 'POST' });
  },

  // Mark email as unread
  markAsUnread: async (emailId: string) => {
    return apiCall(`/emails/${emailId}/unread`, { method: 'POST' });
  },

  // Perform a generic action on an email
  performEmailAction: async (emailId: string, action: string, value?: any): Promise<any> => {
    console.log(`🔧 API - performEmailAction called: ${action} on email ${emailId}`);
    console.log(`🔧 API - Request body:`, { action, value });
    const response = await apiCall(`/emails/${emailId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, value }),
    });
    console.log(`🔧 API - Response:`, response);
    return response;
  },

  // Add tags to email
  addTags: async (emailId: string, tags: string[]) => {
    return apiCall(`/emails/${emailId}/tags`, {
      method: 'POST',
      body: JSON.stringify({ tags }),
    });
  },

  // Get email statistics
  getStats: async () => {
    return apiCall('/emails/stats');
  },

  // Fetch emails from all accounts
  fetchEmails: async (params: { limit?: number } = {}) => {
    return apiCall('/emails/fetch', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  // Get email accounts
  getAccounts: async () => {
    return apiCall('/emails/accounts');
  },

  // Test email accounts
  testAccounts: async () => {
    return apiCall('/emails/accounts/test', {
      method: 'POST',
    });
  },

  // Mark all emails as read
  markAllAsRead: async () => {
    return apiCall('/emails/mark_all_read', {
      method: 'POST',
    });
  },

  // Batch categorize emails
  categorizeBatch: async (params: {
    email_ids?: string[];
    limit?: number;
    priority?: 'recent' | 'unread' | 'all';
  } = {}) => {
    return apiCall('/emails/categorize/batch', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  // Get uncategorized emails
  getUncategorized: async (params: {
    limit?: number;
    priority?: 'unread' | 'recent' | 'all';
  } = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    return apiCall(`/emails/categorize/uncategorized?${searchParams.toString()}`);
  },

  // Get main categories
  getMainCategories: async () => {
    return apiCall('/emails/categories/main');
  },

  // Get sub categories for a main category
  getSubCategories: async (mainCategory: string) => {
    return apiCall(`/emails/categories/${mainCategory}/sub`);
  },

  // Get emails by main category
  getEmailsByMainCategory: async (mainCategory: string, params: {
    page?: number;
    per_page?: number;
    account_email?: string;
  } = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    return apiCall(`/emails/categories/${mainCategory}?${searchParams.toString()}`);
  },

  // Get emails by category hierarchy
  getEmailsByCategoryHierarchy: async (mainCategory: string, subCategory: string, params: {
    page?: number;
    per_page?: number;
    account_email?: string;
  } = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    return apiCall(`/emails/categories/${mainCategory}/${subCategory}?${searchParams.toString()}`);
  },

  // Get all categories
  getCategories: async () => {
    return apiCall('/emails/categories');
  },

  getEmailById: async (id: string): Promise<Email> => {
    const response = await apiCall(`/emails/${id}`);
    return response;
  },
};

// Settings API
export const settingsAPI = {
  // Get all email accounts
  getEmailAccounts: async () => {
    return apiCall('/settings/email-accounts');
  },

  // Add new email account
  addEmailAccount: async (account: {
    email: string;
    password: string;
    imap_server?: string;
    imap_port?: number;
  }) => {
    return apiCall('/settings/email-accounts', {
      method: 'POST',
      body: JSON.stringify(account),
    });
  },

  // Delete email account
  deleteEmailAccount: async (email: string) => {
    return apiCall(`/settings/email-accounts/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  },

  // Test email account
  testEmailAccount: async (email: string) => {
    return apiCall(`/settings/email-accounts/${encodeURIComponent(email)}/test`, {
      method: 'POST',
    });
  },

  // Test all email accounts
  testAllEmailAccounts: async () => {
    return apiCall('/settings/email-accounts/test-all', {
      method: 'POST',
    });
  },

  // Update email account
  updateEmailAccount: async (email: string, updates: {
    password?: string;
    imap_server?: string;
    imap_port?: number;
    is_active?: boolean;
  }) => {
    return apiCall(`/settings/email-accounts/${encodeURIComponent(email)}/update`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },
};

// Admin API
export const adminAPI = {
  // Get all users (admin only)
  getUsers: async () => {
    return apiCall('/admin/users');
  },

  // Update user status (admin only)
  updateUserStatus: async (userId: string, isActive: boolean) => {
    return apiCall(`/admin/users/${userId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    });
  },

  // Get category management info (admin only)
  getCategoryManagement: async () => {
    return apiCall('/admin/categories');
  },

  // Update category rules (admin only)
  updateCategoryRules: async (category: string, rules: {
    keywords: string[];
    sender_patterns: string[];
    priority: number;
  }) => {
    return apiCall(`/admin/categories/${category}`, {
      method: 'PUT',
      body: JSON.stringify(rules),
    });
  },

  // Delete category (admin only)
  deleteCategory: async (category: string) => {
    return apiCall(`/admin/categories/${category}`, {
      method: 'DELETE',
    });
  },

  // Reset categorization stats (admin only)
  resetCategorizationStats: async () => {
    return apiCall('/admin/categories/stats/reset', {
      method: 'POST',
    });
  },

  // Get system status (admin only)
  getSystemStatus: async () => {
    return apiCall('/admin/system/status');
  },

  // Clear email storage (admin only)
  clearEmailStorage: async () => {
    return apiCall('/admin/storage/clear', {
      method: 'POST',
    });
  },
};

// Notification API
export const notificationAPI = {
  // Get notifications
  getNotifications: async () => {
    return apiCall('/notifications/');
  },

  // Mark notification as read
  markAsRead: async (notificationId: string) => {
    return apiCall(`/notifications/${notificationId}/read/`, {
      method: 'POST',
    });
  },

  // Mark all notifications as read
  markAllAsRead: async () => {
    return apiCall('/notifications/mark-all-read/', {
      method: 'POST',
    });
  },

  // Delete notification
  deleteNotification: async (notificationId: string) => {
    return apiCall(`/notifications/${notificationId}/`, {
      method: 'DELETE',
    });
  },
};

// Reply API
export const replyAPI = {
  // Get reply templates
  getTemplates: async () => {
    return apiCall('/replies/templates');
  },

  // Create reply template
  createTemplate: async (template: {
    name: string;
    subject: string;
    body: string;
    category?: string;
  }) => {
    return apiCall('/replies/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    });
  },

  // Update reply template
  updateTemplate: async (templateId: string, updates: {
    name?: string;
    subject?: string;
    body?: string;
    category?: string;
  }) => {
    return apiCall(`/replies/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },

  // Delete reply template
  deleteTemplate: async (templateId: string) => {
    return apiCall(`/replies/templates/${templateId}`, {
      method: 'DELETE',
    });
  },

  // Send reply
  sendReply: async (emailId: string, reply: {
    subject: string;
    body: string;
    template_id?: string;
  }) => {
    return apiCall(`/replies/send/${emailId}`, {
      method: 'POST',
      body: JSON.stringify(reply),
    });
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    return apiCall('/health');
  },
};

// Legacy API exports for backward compatibility
export const emailAccountAPI = {
  getAccounts: emailAPI.getAccounts,
  testAccounts: emailAPI.testAccounts,
};

export const emailFetchAPI = {
  fetchEmails: emailAPI.fetchEmails,
};

export const emailStatsAPI = {
  getStats: emailAPI.getStats,
};

export const categoryAPI = {
  getCategories: emailAPI.getCategories,
  getMainCategories: emailAPI.getMainCategories,
  getSubCategories: emailAPI.getSubCategories,
  getEmailsByMainCategory: emailAPI.getEmailsByMainCategory,
  getEmailsByCategoryHierarchy: emailAPI.getEmailsByCategoryHierarchy,
};

export const categorizationAPI = {
  categorizeBatch: emailAPI.categorizeBatch,
  getUncategorizedEmails: emailAPI.getUncategorized,
};

// Combined API object for easy imports
export const api = {
  auth: authAPI,
  emails: emailAPI,
  settings: settingsAPI,
  admin: adminAPI,
  notifications: notificationAPI,
  replies: replyAPI,
  health: healthAPI,
  // Legacy exports
  accounts: emailAccountAPI,
  fetch: emailFetchAPI,
  stats: emailStatsAPI,
  categories: categoryAPI,
  categorization: categorizationAPI,
}; 