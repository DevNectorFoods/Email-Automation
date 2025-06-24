import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Star, StarOff, Archive, Trash2, Reply, Forward, MoreHorizontal, Mail, XCircle } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import EmailDrawer from "./EmailDrawer";

interface Email {
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

interface EmailListProps {
  emails: Email[];
  onEmailClick?: (email: Email) => void;
  markAsUnread: (emailId: string) => void;
  performAction: (emailId: string, action: string, value?: any) => void;
  currentFolder?: string;
}

export default function EmailList({ emails, onEmailClick, markAsUnread, performAction, currentFolder }: EmailListProps) {
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [hoveredEmail, setHoveredEmail] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Safety check for performAction
  const safePerformAction = performAction || ((emailId: string, action: string, value?: any) => {
    console.warn(`performAction is not available on EmailList. Action "${action}" not performed.`);
  });

  const getCategoryColor = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'work':
        return 'bg-blue-100 text-blue-800';
      case 'personal':
        return 'bg-green-100 text-green-800';
      case 'newsletter':
        return 'bg-purple-100 text-purple-800';
      case 'billing':
      case 'billing/finance':
        return 'bg-yellow-100 text-yellow-800';
      case 'notification':
        return 'bg-orange-100 text-orange-800';
      case 'complaint':
        return 'bg-red-100 text-red-800';
      case 'inquiry':
        return 'bg-cyan-100 text-cyan-800';
      case 'follow-up':
        return 'bg-indigo-100 text-indigo-800';
      case 'spam':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getInitials = (sender: string) => {
    const words = sender.split(' ');
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return sender.slice(0, 2).toUpperCase();
  };

  const getAvatarColor = (sender: string) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-green-500 to-green-600',
      'from-purple-500 to-purple-600',
      'from-red-500 to-red-600',
      'from-yellow-500 to-yellow-600',
      'from-indigo-500 to-indigo-600',
      'from-pink-500 to-pink-600',
      'from-teal-500 to-teal-600',
    ];
    const index = sender.length % colors.length;
    return colors[index];
  };

  const formatTimeAgo = (date: string | Date) => {
    const now = new Date();
    const emailDate = new Date(date);
    const diff = now.getTime() - emailDate.getTime();
    
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return `${days}d ago`;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    // Strip HTML tags for preview
    const cleanText = text.replace(/<[^>]*>/g, '');
    if (cleanText.length <= maxLength) return cleanText;
    return cleanText.slice(0, maxLength) + '...';
  };

  const handleEmailClick = (email: Email) => {
    setSelectedEmail(email);
    if (onEmailClick) {
      onEmailClick(email);
    }
  };

  const handleCheckboxChange = (id: string, checked: boolean) => {
    setSelectedIds(prev =>
      checked ? [...prev, id] : prev.filter(eid => eid !== id)
    );
  };

  const handleDelete = (emailId: string) => {
    console.log('🗑️ EmailList - Delete button clicked for email:', emailId);
    console.log('🗑️ EmailList - performAction type:', typeof performAction);
    console.log('🗑️ EmailList - performAction function:', performAction);
    console.log('🗑️ EmailList - safePerformAction function:', safePerformAction);
    safePerformAction(emailId, 'trash');
  };

  const handlePermanentDelete = async (emailId: string) => {
    if (!window.confirm('Are you sure you want to permanently delete this email? This cannot be undone.')) return;
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/emails/${emailId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(errorData.error || 'Failed to permanently delete email');
      } else {
        // Optionally, refresh the list or call a callback
        window.location.reload();
      }
    } catch (err) {
      alert('Failed to permanently delete email');
    }
  };

  if (!emails || emails.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No emails found</p>
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 overflow-x-hidden h-full relative">
      {/* Inbox List or Email View (Gmail style) */}
      <div className="flex-1 transition-all duration-200">
        {!selectedEmail ? (
          <div className="email-list-container divide-y divide-gray-100">
            {emails.map((email) => (
              <div
                key={email.id}
                className={`group flex items-center w-full min-w-0 px-4 py-2 border-b border-gray-100 cursor-pointer transition-colors ${!email.is_read ? 'bg-blue-50' : 'bg-white'} hover:bg-gray-100`}
                onClick={() => handleEmailClick(email)}
                onMouseEnter={() => setHoveredEmail(email.id)}
                onMouseLeave={() => setHoveredEmail(null)}
                style={{ fontFamily: 'sans-serif', fontSize: '15px' }}
              >
                {/* Checkbox */}
                <div className="flex-shrink-0 mr-2">
                  <Checkbox
                    checked={selectedIds.includes(email.id)}
                    onCheckedChange={checked => handleCheckboxChange(email.id, !!checked)}
                    onClick={e => e.stopPropagation()}
                    aria-label="Select email"
                  />
                </div>
                {/* Star icon */}
                <button
                  className="flex-shrink-0 p-1 mr-3 rounded hover:bg-gray-200"
                  onClick={e => {
                    e.stopPropagation();
                    safePerformAction(email.id, 'star');
                  }}
                  aria-label="Star email"
                >
                  <Star className={`h-4 w-4 ${email.is_starred ? 'text-yellow-400' : 'text-gray-300'}`} />
                </button>
                {/* Sender */}
                <div className={`truncate mr-4 flex-shrink-0 w-40 ${!email.is_read ? 'font-bold text-gray-900' : 'font-medium text-gray-700'}`}>
                  {email.sender.split('<')[0].trim() || email.sender}
                </div>
                {/* Subject and preview (Gmail-style, single-line truncate) */}
                <div className="flex-1 min-w-0 flex items-center">
                  <span
                    className={`block w-full truncate whitespace-nowrap overflow-hidden text-ellipsis ${!email.is_read ? 'font-bold' : 'font-normal'} text-gray-900`}
                  >
                    {email.subject}
                    <span className="text-gray-500 font-normal text-sm"> - {truncateText(email.body, 60)}</span>
                  </span>
                </div>
                {/* Date/Time or Hover Actions */}
                <div className="text-xs text-gray-500 ml-4 flex-shrink-0 w-20 text-right">
                  {hoveredEmail === email.id ? (
                    <div className="flex items-center justify-end space-x-4">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={e => {
                          e.stopPropagation();
                          safePerformAction(email.id, 'archive');
                        }}
                      >
                        <Archive className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={e => {
                          e.stopPropagation();
                          handleDelete(email.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      {currentFolder === 'trash' && (
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={e => {
                            e.stopPropagation();
                            handlePermanentDelete(email.id);
                          }}
                          title="Delete Forever"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={e => {
                          e.stopPropagation();
                          markAsUnread(email.id);
                        }}
                      >
                        <Mail className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    formatTimeAgo(email.date)
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-[80vh] flex flex-col">
            <EmailDrawer
              email={selectedEmail}
              emailList={emails}
              currentIndex={emails.findIndex(e => e.id === selectedEmail.id)}
              onClose={() => setSelectedEmail(null)}
              onNavigate={idx => setSelectedEmail(emails[idx])}
              markAsUnread={markAsUnread}
              performAction={safePerformAction}
            />
          </div>
        )}
      </div>

      {selectedEmail && (
        <div className="absolute inset-0 bg-white z-20">
          <EmailDrawer
            email={selectedEmail}
            emailList={emails}
            currentIndex={emails.findIndex(e => e.id === selectedEmail.id)}
            onClose={() => setSelectedEmail(null)}
            onNavigate={(idx) => setSelectedEmail(emails[idx])}
            markAsUnread={markAsUnread}
            performAction={safePerformAction}
          />
        </div>
      )}
    </div>
  );
}
