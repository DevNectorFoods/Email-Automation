import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Archive, Trash2, Mail, Star, Reply, Forward, MoreHorizontal, Printer, Tag, ArrowLeft, ArrowRight, AlertCircle, Move, Eye, ExternalLink, Circle, User, ChevronDown } from "lucide-react";
import DOMPurify from "dompurify";

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
  tags: string[];
  metadata: any;
  created_at: string;
  is_starred: boolean;
}

interface EmailDrawerProps {
  email: Email;
  emailList: Email[];
  currentIndex: number;
  onClose: () => void;
  onNavigate: (idx: number) => void;
  markAsUnread: (emailId: string) => void;
  performAction: (emailId: string, action: string, value?: any) => void;
}

const sanitizeHtml = (html: string): string => {
  const config = {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'img', 'table', 'tr', 'td', 'th',
      'thead', 'tbody', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'blockquote', 'div', 'span', 'hr', 'pre', 'code'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'width', 'height', 'style', 'class', 'id',
      'target', 'rel', 'border', 'cellpadding', 'cellspacing', 'align', 'valign'
    ],
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp):|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i,
    KEEP_CONTENT: true,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false,
    RETURN_TRUSTED_TYPE: false
  };
  return DOMPurify.sanitize(html, config);
};

// Helper: Linkify plain text URLs
function linkify(text: string): string {
  // Regex for URLs
  const urlRegex = /(https?:\/\/[\w\-._~:/?#[\]@!$&'()*+,;=%]+)|(www\.[\w\-._~:/?#[\]@!$&'()*+,;=%]+)/gi;
  return text.replace(urlRegex, (url) => {
    let href = url;
    if (!href.startsWith('http')) href = 'http://' + href;
    // Shorten link text if too long
    let display = url;
    if (url.length > 40) {
      display = url.slice(0, 30) + '...' + url.slice(-10);
    }
    // Tooltip with full link
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" title="${url}">${display}</a>`;
  });
}

// Helper: Format plain text as paragraphs with line breaks
function formatPlainText(text: string): string {
  // First, linkify
  let linked = linkify(text);
  // Split on double line breaks for paragraphs
  const paragraphs = linked.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  // Wrap each paragraph in <p> and replace single \n with <br>
  return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

// Helper: Convert email thread to Gmail-style blockquotes
function threadToBlockquote(text: string): string {
  // Regex to match 'On ... wrote:' lines
  const threadRegex = /^On .+ wrote:$/gm;
  let result = '';
  let lastIndex = 0;
  let match;
  let openBlockquotes = 0;
  // Find all thread starts
  while ((match = threadRegex.exec(text)) !== null) {
    // Close previous blockquote if open
    if (openBlockquotes > 0) {
      result += '</blockquote>';
      openBlockquotes--;
    }
    // Add text before this match
    result += text.slice(lastIndex, match.index);
    // Open new blockquote
    result += `<blockquote>${match[0]}`;
    openBlockquotes++;
    lastIndex = match.index + match[0].length;
  }
  // Add remaining text
  result += text.slice(lastIndex);
  // Close any open blockquotes
  while (openBlockquotes > 0) {
    result += '</blockquote>';
    openBlockquotes--;
  }
  return result;
}

export default function EmailDrawer({ email, emailList, currentIndex, onClose, onNavigate, markAsUnread, performAction }: EmailDrawerProps) {
  console.log('EmailDrawer props:', { email, performAction: typeof performAction });
  const [showDetails, setShowDetails] = useState(false);
  
  // Safety check for performAction - if it's undefined, we'll use a no-op function
  const safePerformAction = performAction || ((emailId: string, action: string, value?: any) => {
    console.warn('performAction is not available - this should not happen');
  });
  
  // Detect if body is HTML or plain text
  const isHtml = /<\s*\w+.*?>/.test(email.body);
  let displayBody = '';
  if (isHtml) {
    displayBody = sanitizeHtml(email.body);
  } else {
    displayBody = sanitizeHtml(formatPlainText(email.body));
  }
  // Gmail-style thread blockquote
  displayBody = threadToBlockquote(displayBody);
  const hasContent = displayBody.trim().length > 0;
  const attachments = Array.isArray(email.metadata?.attachments) ? email.metadata.attachments : [];
  const formatDate = (date: string) => new Date(date).toLocaleString();

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Print Email - ${email.subject}</title>
            <style>
              body { font-family: sans-serif; }
              h1 { font-size: 22px; }
              .meta { margin-bottom: 20px; font-size: 14px; color: #555; }
              .meta div { margin-bottom: 5px; }
              .body { margin-top: 20px; }
            </style>
          </head>
          <body>
            <h1>${email.subject}</h1>
            <div class="meta">
              <div><strong>From:</strong> ${email.sender}</div>
              <div><strong>To:</strong> ${email.account_email}</div>
              <div><strong>Date:</strong> ${formatDate(email.date)}</div>
            </div>
            <hr />
            <div class="body">
              ${displayBody}
            </div>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }
  };

  const handleOpenInNewWindow = () => {
    const newWindow = window.open('', '_blank');
    if (newWindow) {
      newWindow.document.write(`
        <html>
          <head>
            <title>${email.subject}</title>
            <style>
              body { font-family: sans-serif; padding: 20px; }
              h1 { font-size: 24px; }
              .meta { margin-bottom: 20px; font-size: 14px; color: #555; border-bottom: 1px solid #eee; padding-bottom: 15px; }
              .meta div { margin-bottom: 5px; }
              .body { margin-top: 20px; line-height: 1.6; }
            </style>
          </head>
          <body>
            <h1>${email.subject}</h1>
            <div class="meta">
              <div><strong>From:</strong> ${email.sender}</div>
              <div><strong>To:</strong> ${email.account_email}</div>
              <div><strong>Date:</strong> ${formatDate(email.date)}</div>
            </div>
            <div class="body">
              ${displayBody}
            </div>
          </body>
        </html>
      `);
      newWindow.document.close();
    }
  };

  const handleDelete = () => {
    console.log('🗑️ EmailDrawer - Delete button clicked for email:', email.id);
    console.log('🗑️ EmailDrawer - performAction type:', typeof performAction);
    console.log('🗑️ EmailDrawer - performAction function:', performAction);
    console.log('🗑️ EmailDrawer - safePerformAction function:', safePerformAction);
    safePerformAction(email.id, 'trash');
  };

  // Helper for avatar fallback
  const getInitials = (sender: string) => {
    const words = sender.split(' ');
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return sender.slice(0, 2).toUpperCase();
  };

  return (
    <div className="bg-white rounded-xl shadow-lg h-full flex flex-col w-full max-w-full min-w-0 overflow-x-hidden">
      {/* Navigation Bar - sticky top-0 */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-white sticky top-0 z-20 w-full max-w-full overflow-x-hidden">
        <div className="flex items-center space-x-1">
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100" title="Back"><ArrowLeft className="w-5 h-5" /></button>
          
          <div className="flex items-center space-x-1 ml-4">
            <button onClick={() => safePerformAction(email.id, 'archive')} className="p-2 rounded-full hover:bg-gray-100" title="Archive"><Archive className="w-5 h-5" /></button>
            <button onClick={() => safePerformAction(email.id, 'report_spam')} className="p-2 rounded-full hover:bg-gray-100" title="Report Spam"><AlertCircle className="w-5 h-5" /></button>
            <button onClick={handleDelete} className="p-2 rounded-full hover:bg-gray-100" title="Delete"><Trash2 className="w-5 h-5" /></button>
          </div>

          <span className="border-l h-5 mx-2"></span>
          
          <div className="flex items-center space-x-1">
            <button onClick={() => markAsUnread(email.id)} className="p-2 rounded-full hover:bg-gray-100" title="Mark as unread"><Mail className="w-5 h-5" /></button>
          </div>

          <span className="border-l h-5 mx-2"></span>

          <div className="flex items-center space-x-1">
            <button className="p-2 rounded-full hover:bg-gray-100" title="Move to"><Move className="w-5 h-5" /></button>
            <button className="p-2 rounded-full hover:bg-gray-100" title="Labels"><Tag className="w-5 h-5" /></button>
          </div>
          
          <span className="border-l h-5 mx-2"></span>

          <button className="p-2 rounded-full hover:bg-gray-100" title="More"><MoreHorizontal className="w-5 h-5" /></button>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>{currentIndex + 1} of {emailList.length}</span>
          <button onClick={() => onNavigate(currentIndex - 1)} disabled={currentIndex <= 0} className="p-1 rounded-full hover:bg-gray-100 disabled:opacity-40" title="Previous"><ArrowLeft className="w-5 h-5" /></button>
          <button onClick={() => onNavigate(currentIndex + 1)} disabled={currentIndex >= emailList.length - 1} className="p-1 rounded-full hover:bg-gray-100 disabled:opacity-40" title="Next"><ArrowRight className="w-5 h-5" /></button>
        </div>
      </div>
      {/* Scrollable area: subject/sender info + email body */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-8 pt-6 pb-2 border-b border-gray-100 bg-white">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center min-w-0">
              <span className="text-2xl font-bold text-gray-900 mr-3 truncate">{email.subject || '(No Subject)'}</span>
              <span className="ml-2 px-2 py-0.5 bg-gray-100 text-xs text-gray-700 rounded-full flex-shrink-0">Inbox</span>
            </div>
            <div className="flex items-center space-x-1 flex-shrink-0">
              <button onClick={handlePrint} className="p-2 rounded-full hover:bg-gray-100" title="Print"><Printer className="w-5 h-5" /></button>
              <button onClick={handleOpenInNewWindow} className="p-2 rounded-full hover:bg-gray-100" title="Open in new window"><ExternalLink className="w-5 h-5" /></button>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-lg font-bold text-gray-500">
                <User className="w-7 h-7" />
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-gray-900 leading-tight">{email.sender.split('<')[0].trim() || email.sender}</span>
                <span className="text-xs text-gray-500">{email.sender.includes('<') ? email.sender.split('<')[1].replace('>', '') : email.sender}</span>
                <div className="flex items-center text-xs text-gray-500">
                  <span>to me</span>
                  <button onClick={() => setShowDetails(!showDetails)} className="ml-1 rounded-full p-1 hover:bg-gray-100 flex items-center">
                    <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${showDetails ? 'rotate-180' : ''}`} />
                  </button>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">{formatDate(email.date)}</span>
              <button onClick={() => safePerformAction(email.id, 'star')} className="p-1 rounded-full hover:bg-gray-100" title="Star">
                <Star className={`w-5 h-5 ${email.is_starred ? 'text-yellow-400 fill-current' : 'text-gray-400'}`} />
              </button>
              <button className="p-1 rounded-full hover:bg-gray-100" title="Reply"><Reply className="w-5 h-5 text-gray-400" /></button>
              <button className="p-1 rounded-full hover:bg-gray-100" title="More"><MoreHorizontal className="w-5 h-5 text-gray-400" /></button>
            </div>
          </div>
        </div>
        
        {/* Expanded Details View */}
        {showDetails && (
          <div className="px-8 py-4 border-b border-gray-100 bg-gray-50 text-xs">
            <table className="w-full">
              <tbody>
                <tr className="hover:bg-gray-100">
                  <td className="py-1 pr-2 font-medium text-gray-500 align-top">From:</td>
                  <td className="py-1 text-gray-800">{email.sender}</td>
                </tr>
                <tr className="hover:bg-gray-100">
                  <td className="py-1 pr-2 font-medium text-gray-500 align-top">To:</td>
                  <td className="py-1 text-gray-800">{email.account_email}</td>
                </tr>
                <tr className="hover:bg-gray-100">
                  <td className="py-1 pr-2 font-medium text-gray-500 align-top">Date:</td>
                  <td className="py-1 text-gray-800">{formatDate(email.date)}</td>
                </tr>
                <tr className="hover:bg-gray-100">
                  <td className="py-1 pr-2 font-medium text-gray-500 align-top">Subject:</td>
                  <td className="py-1 text-gray-800">{email.subject}</td>
                </tr>
                {email.metadata?.mailed_by && (
                  <tr className="hover:bg-gray-100">
                    <td className="py-1 pr-2 font-medium text-gray-500 align-top">Mailed-by:</td>
                    <td className="py-1 text-gray-800">{email.metadata.mailed_by}</td>
                  </tr>
                )}
                {email.metadata?.signed_by && (
                  <tr className="hover:bg-gray-100">
                    <td className="py-1 pr-2 font-medium text-gray-500 align-top">Signed-by:</td>
                    <td className="py-1 text-gray-800">{email.metadata.signed_by}</td>
                  </tr>
                )}
                {email.metadata?.security && (
                  <tr className="hover:bg-gray-100">
                    <td className="py-1 pr-2 font-medium text-gray-500 align-top">Security:</td>
                    <td className="py-1 text-gray-800">{email.metadata.security}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Email Body (scrollable) */}
        <div className="px-8 py-6 bg-white">
          {/* Attachments (if any) */}
          {attachments.length > 0 && (
            <div className="mb-4">
              <div className="font-medium text-gray-700 mb-2">Attachments:</div>
              <div className="flex space-x-3 overflow-x-auto pb-2">
                {attachments.map((att: any, idx: number) => (
                  <a
                    key={att.filename || idx}
                    href={`/api/emails/${email.id}/attachments/${encodeURIComponent(att.filename)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-2 bg-gray-100 hover:bg-blue-100 rounded text-blue-700 text-sm font-medium border border-gray-200 whitespace-nowrap"
                    download={att.filename}
                  >
                    <span className="truncate max-w-[120px]">{att.filename}</span>
                    {att.size && (
                      <span className="ml-2 text-xs text-gray-500">({(att.size/1024).toFixed(1)} KB)</span>
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}
          <div className="prose prose-sm sm:prose lg:prose-lg max-w-full text-gray-900 font-sans leading-relaxed break-words">
            {hasContent ? (
              <div
                dangerouslySetInnerHTML={{ __html: displayBody }}
              />
            ) : (
              <p>No content found in the email body.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 