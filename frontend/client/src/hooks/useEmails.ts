import { useState, useEffect, useCallback } from 'react';
import { emailAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Email, EmailFilters } from '@/types';

export interface EmailStats {
  total_emails: number;
  total_accounts: number;
  unread_emails: number;
  emails_by_category: Record<string, number>;
  emails_by_account: Record<string, number>;
  last_fetch_time: string;
  fetch_errors: number;
}

// Hook for fetching emails with filters
export const useEmails = (initialFilters: Partial<EmailFilters> = {}) => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Partial<EmailFilters>>(initialFilters);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  });
  const { user } = useAuth();

  // Update filters when initialFilters change
  useEffect(() => {
    setFilters(initialFilters);
  }, [JSON.stringify(initialFilters)]);

  const performAction = useCallback(async (emailId: string, action: string, value?: any) => {
    console.log(`🔧 useEmails - performAction called: ${action} on email ${emailId}`);
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication token not found.");
      return;
    }
    try {
      const response = await emailAPI.performEmailAction(emailId, action, value);
      console.log(`🔧 useEmails - API response:`, response);
      if (response) {
        // Refetch emails and trigger stats refresh
        refetch(); 
        // Trigger stats refresh by dispatching a custom event
        console.log('🔄 useEmails - Dispatching refreshEmailStats event');
        window.dispatchEvent(new CustomEvent('refreshEmailStats'));
        // Also trigger stats refresh directly after a short delay
        setTimeout(() => {
          console.log('🔄 useEmails - Direct stats refresh after delay');
          window.dispatchEvent(new CustomEvent('refreshEmailStats'));
        }, 500);
      }
    } catch (err: any) {
      console.error("Failed to perform email action:", err);
      setError(err.response?.data?.error || 'An error occurred.');
    }
  }, [user]);

  const fetchEmails = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication token not found.");
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      console.log('🔧 useEmails - Fetching emails with filters:', filters);
      const response = await emailAPI.getEmails({
        ...filters,
        page: filters.page || 1,
      });
      console.log('🔧 useEmails - Received emails:', response.emails.length);
      setEmails(response.emails);
      setPagination(response.pagination);
    } catch (err: any) {
      console.error("Failed to fetch emails:", err);
      setError(err.response?.data?.error || 'An error occurred while fetching emails.');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    fetchEmails();
  }, [fetchEmails]);

  // Refetch always uses latest filters from initialFilters
  const refetch = useCallback(() => {
    console.log('🔄 useEmails - refetch called with filters:', initialFilters);
    setFilters({ ...initialFilters });
    fetchEmails();
  }, [JSON.stringify(initialFilters), fetchEmails]);

  const markAsRead = async (emailId: string) => {
    try {
      await emailAPI.markAsRead(emailId);
      // Update local state
      setEmails(prev => prev.map(email => 
        email.id === emailId ? { ...email, is_read: true } : email
      ));
    } catch (err) {
      console.error('Failed to mark email as read:', err);
    }
  };

  const markAsUnread = useCallback(async (emailId: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      await emailAPI.markAsUnread(emailId);
      // Update local state
      setEmails(prev => prev.map(email => 
        email.id === emailId ? { ...email, is_read: false } : email
      ));
    } catch (err) {
      console.error('Failed to mark email as unread:', err);
    }
  }, []);

  const addTags = async (emailId: string, tags: string[]) => {
    try {
      await emailAPI.addTags(emailId, tags);
      // Update local state
      setEmails(prev => prev.map(email => 
        email.id === emailId ? { ...email, tags: [...email.tags, ...tags] } : email
      ));
    } catch (err) {
      console.error('Failed to add tags:', err);
    }
  };

  return {
    emails,
    loading,
    error,
    pagination,
    filters,
    setFilters,
    refetch,
    markAsRead,
    markAsUnread,
    performAction,
    addTags,
  };
};

// Hook for email statistics
export const useEmailStats = () => {
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getStats();
      setStats(response.stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
};

// Hook for fetching emails
export const useEmailFetch = () => {
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const fetchEmails = async (limit?: number) => {
    try {
      setFetching(true);
      setError(null);
      
      const response = await emailAPI.fetchEmails({ limit });
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch emails';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setFetching(false);
    }
  };

  return {
    fetching,
    error,
    result,
    fetchEmails,
  };
};

// Hook for single email
export const useEmail = (emailId: string) => {
  const [email, setEmail] = useState<Email | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmail = async () => {
    if (!emailId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getEmail(emailId);
      setEmail(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch email');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmail();
  }, [emailId]);

  return {
    email,
    loading,
    error,
    refetch: fetchEmail,
  };
}; 