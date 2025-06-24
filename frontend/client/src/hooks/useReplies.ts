import { useState, useEffect } from 'react';
import { replyAPI } from '@/lib/api';

export interface ReplyTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  category?: string;
  created_at: string;
  updated_at: string;
}

// Hook for reply templates
export const useReplyTemplates = () => {
  const [templates, setTemplates] = useState<ReplyTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await replyAPI.getTemplates();
      setTemplates(response.templates || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reply templates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const createTemplate = async (template: {
    name: string;
    subject: string;
    body: string;
    category?: string;
  }) => {
    try {
      await replyAPI.createTemplate(template);
      await fetchTemplates(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to create reply template');
    }
  };

  const updateTemplate = async (templateId: string, updates: {
    name?: string;
    subject?: string;
    body?: string;
    category?: string;
  }) => {
    try {
      await replyAPI.updateTemplate(templateId, updates);
      await fetchTemplates(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to update reply template');
    }
  };

  const deleteTemplate = async (templateId: string) => {
    try {
      await replyAPI.deleteTemplate(templateId);
      await fetchTemplates(); // Refresh the list
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to delete reply template');
    }
  };

  return {
    templates,
    loading,
    error,
    refetch: fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
  };
};

// Hook for sending replies
export const useSendReply = () => {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const sendReply = async (emailId: string, reply: {
    subject: string;
    body: string;
    template_id?: string;
  }) => {
    try {
      setSending(true);
      setError(null);
      
      const response = await replyAPI.sendReply(emailId, reply);
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send reply';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setSending(false);
    }
  };

  return {
    sending,
    error,
    result,
    sendReply,
  };
}; 