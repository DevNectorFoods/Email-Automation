import { useState, useEffect } from 'react';
import { emailAPI } from '@/lib/api';

export interface Category {
  main_category: string;
  count: number;
}

export interface SubCategory {
  sub_category: string;
  count: number;
}

export interface Email {
  id: string;
  account_email: string;
  subject: string;
  sender: string;
  date: string;
  body: string;
  category: string;
  main_category: string;
  sub_category: string;
  is_read: boolean;
  tags: string[];
  metadata: any;
  created_at: string;
}

// Hook for main categories
export const useMainCategories = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getMainCategories();
      setCategories(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  return {
    categories,
    loading,
    error,
    refetch: fetchCategories,
  };
};

// Hook for sub categories
export const useSubCategories = (mainCategory: string) => {
  const [subCategories, setSubCategories] = useState<SubCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubCategories = async () => {
    if (!mainCategory) {
      setSubCategories([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getSubCategories(mainCategory);
      setSubCategories(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sub categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubCategories();
  }, [mainCategory]);

  return {
    subCategories,
    loading,
    error,
    refetch: fetchSubCategories,
  };
};

// Hook for emails by main category
export const useEmailsByMainCategory = (mainCategory: string, filters: {
  page?: number;
  per_page?: number;
  account_email?: string;
} = {}) => {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  });

  const fetchEmails = async () => {
    if (!mainCategory) {
      setEmails([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getEmailsByMainCategory(mainCategory, {
        page: filters.page || 1,
        per_page: filters.per_page || 20,
        account_email: filters.account_email,
      });

      setEmails(response.emails || []);
      setPagination(response.pagination || {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch emails');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, [mainCategory, filters.page, filters.per_page, filters.account_email]);

  return {
    emails,
    loading,
    error,
    pagination,
    refetch: fetchEmails,
  };
};

// Hook for emails by category hierarchy
export const useEmailsByCategoryHierarchy = (mainCategory: string, subCategory: string, filters: {
  page?: number;
  per_page?: number;
  account_email?: string;
} = {}) => {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  });

  const fetchEmails = async () => {
    if (!mainCategory || !subCategory) {
      setEmails([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getEmailsByCategoryHierarchy(mainCategory, subCategory, {
        page: filters.page || 1,
        per_page: filters.per_page || 20,
        account_email: filters.account_email,
      });

      setEmails(response.emails || []);
      setPagination(response.pagination || {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch emails');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, [mainCategory, subCategory, filters.page, filters.per_page, filters.account_email]);

  return {
    emails,
    loading,
    error,
    pagination,
    refetch: fetchEmails,
  };
};

// Hook for batch categorization
export const useBatchCategorization = () => {
  const [categorizing, setCategorizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const categorizeBatch = async (params?: {
    email_ids?: string[];
    limit?: number;
    priority?: 'recent' | 'unread' | 'all';
  }) => {
    try {
      setCategorizing(true);
      setError(null);
      
      const response = await emailAPI.categorizeBatch(params);
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to categorize emails';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setCategorizing(false);
    }
  };

  return {
    categorizing,
    error,
    result,
    categorizeBatch,
  };
};

// Hook for uncategorized emails
export const useUncategorizedEmails = (params?: {
  limit?: number;
  priority?: 'unread' | 'recent' | 'all';
}) => {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUncategorizedEmails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await emailAPI.getUncategorized(params);
      setEmails(response.emails || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch uncategorized emails');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUncategorizedEmails();
  }, [params?.limit, params?.priority]);

  return {
    emails,
    loading,
    error,
    refetch: fetchUncategorizedEmails,
  };
}; 