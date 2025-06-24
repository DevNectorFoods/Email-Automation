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
  is_starred: boolean;
  tags: string[];
  metadata: any;
  created_at: string;
}

export interface EmailFilters {
  page?: number;
  per_page?: number;
  category?: string;
  folder?: string;
  account?: string;
  search?: string;
  main_category?: string;
  sub_category?: string;
} 