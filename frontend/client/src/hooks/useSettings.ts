import { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';

export interface EmailAccount {
  email: string;
  active: boolean;
}

// Hook for email accounts
export const useEmailAccounts = () => {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await settingsAPI.getEmailAccounts();
      setAccounts(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch email accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const addAccount = async (account: {
    email: string;
    password: string;
    imap_server?: string;
    imap_port?: number;
  }) => {
    try {
      await settingsAPI.addEmailAccount(account);
      await fetchAccounts(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to add email account');
    }
  };

  const deleteAccount = async (email: string) => {
    try {
      await settingsAPI.deleteEmailAccount(email);
      await fetchAccounts(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to delete email account');
    }
  };

  const updateAccount = async (email: string, updates: {
    password?: string;
    imap_server?: string;
    imap_port?: number;
    active?: boolean;
  }) => {
    try {
      await settingsAPI.updateEmailAccount(email, updates);
      await fetchAccounts(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to update email account');
    }
  };

  const testAccount = async (email: string) => {
    try {
      await settingsAPI.testEmailAccount(email);
      return true;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to test email account');
    }
  };

  const testAllAccounts = async () => {
    try {
      const response = await settingsAPI.testAllEmailAccounts();
      return response;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to test email accounts');
    }
  };

  return {
    accounts,
    loading,
    error,
    refetch: fetchAccounts,
    addAccount,
    deleteAccount,
    updateAccount,
    testAccount,
    testAllAccounts,
  };
}; 