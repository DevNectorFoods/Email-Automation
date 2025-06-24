import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Folder, 
  FolderOpen, 
  Mail, 
  ChevronRight, 
  ChevronDown,
  Search,
  Filter,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react';
import { useMainCategories, useSubCategories, useEmailsByMainCategory, useEmailsByCategoryHierarchy } from '@/hooks/useCategories';
import { useEmails } from '@/hooks/useEmails';
import EmailList from '@/components/EmailList';

export default function CategoriesPage() {
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [accountFilter, setAccountFilter] = useState<string>('');

  // API hooks
  const { categories, loading: categoriesLoading } = useMainCategories();
  const { subCategories, loading: subCategoriesLoading } = useSubCategories(selectedCategory || '');
  
  // Email hooks based on selection
  const { emails: categoryEmails, loading: categoryEmailsLoading } = useEmailsByMainCategory(
    selectedCategory || '',
    { account_email: accountFilter || undefined }
  );
  
  const { emails: hierarchyEmails, loading: hierarchyEmailsLoading } = useEmailsByCategoryHierarchy(
    selectedCategory || '',
    selectedSubCategory || '',
    { account_email: accountFilter || undefined }
  );

  // Determine which emails to show
  const emails = selectedSubCategory ? hierarchyEmails : categoryEmails;
  const emailsLoading = selectedSubCategory ? hierarchyEmailsLoading : categoryEmailsLoading;

  const handleCategoryClick = (category: string) => {
    if (selectedCategory === category) {
      // Toggle expansion
      const newExpanded = new Set(expandedCategories);
      if (newExpanded.has(category)) {
        newExpanded.delete(category);
        setSelectedSubCategory(null);
      } else {
        newExpanded.add(category);
      }
      setExpandedCategories(newExpanded);
    } else {
      // Select new category
      setSelectedCategory(category);
      setSelectedSubCategory(null);
      const newExpanded = new Set(expandedCategories);
      newExpanded.add(category);
      setExpandedCategories(newExpanded);
    }
  };

  const handleSubCategoryClick = (subCategory: string) => {
    if (selectedSubCategory === subCategory) {
      setSelectedSubCategory(null);
    } else {
      setSelectedSubCategory(subCategory);
    }
  };

  const handleEmailClick = (email: any) => {
    setSelectedEmail(email);
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'bank': return '🏦';
      case 'company': return '🏢';
      case 'support': return '🛠️';
      case 'newsletter': return '📰';
      case 'billing': return '💰';
      case 'order': return '📦';
      case 'social': return '📱';
      case 'security': return '🔒';
      case 'meeting': return '📅';
      case 'career': return '💼';
      case 'notification': return '🔔';
      default: return '📁';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'bank': return 'bg-green-100 text-green-800 border-green-200';
      case 'company': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'support': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'newsletter': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'billing': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'order': return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'social': return 'bg-pink-100 text-pink-800 border-pink-200';
      case 'security': return 'bg-red-100 text-red-800 border-red-200';
      case 'meeting': return 'bg-cyan-100 text-cyan-800 border-cyan-200';
      case 'career': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'notification': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatSubCategoryName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Email Categories</h1>
            <p className="text-gray-600">Browse your emails by categories and folders</p>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Categories Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Folder className="h-5 w-5" />
                  Categories ({categories.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {categoriesLoading ? (
                  <div className="animate-pulse space-y-2">
                    {[1, 2, 3, 4, 5].map(i => (
                      <div key={i} className="h-10 bg-gray-200 rounded"></div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {categories.map((category) => (
                      <div key={category.main_category}>
                        <Button
                          variant={selectedCategory === category.main_category ? "default" : "ghost"}
                          className="w-full justify-between text-left"
                          onClick={() => handleCategoryClick(category.main_category)}
                        >
                          <div className="flex items-center gap-2">
                            {expandedCategories.has(category.main_category) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                            <span className="text-lg">{getCategoryIcon(category.main_category)}</span>
                            <span className="capitalize">{category.main_category}</span>
                          </div>
                          <Badge variant="secondary">{category.count}</Badge>
                        </Button>
                        
                        {/* Sub-categories */}
                        {expandedCategories.has(category.main_category) && (
                          <div className="ml-6 mt-2 space-y-1">
                            {subCategoriesLoading ? (
                              <div className="animate-pulse space-y-1">
                                {[1, 2, 3].map(i => (
                                  <div key={i} className="h-8 bg-gray-200 rounded"></div>
                                ))}
                              </div>
                            ) : (
                              subCategories.map((subCategory) => (
                                <Button
                                  key={subCategory.sub_category}
                                  variant={selectedSubCategory === subCategory.sub_category ? "default" : "ghost"}
                                  size="sm"
                                  className="w-full justify-between text-left text-sm"
                                  onClick={() => handleSubCategoryClick(subCategory.sub_category)}
                                >
                                  <div className="flex items-center gap-2">
                                    <FolderOpen className="h-3 w-3" />
                                    <span className="capitalize">{formatSubCategoryName(subCategory.sub_category)}</span>
                                  </div>
                                  <Badge variant="outline" className="text-xs">{subCategory.count}</Badge>
                                </Button>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Emails Panel */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  {selectedSubCategory ? (
                    <>
                      {selectedCategory} / {formatSubCategoryName(selectedSubCategory)}
                    </>
                  ) : selectedCategory ? (
                    selectedCategory
                  ) : (
                    'Select a category to view emails'
                  )}
                  {emails.length > 0 && (
                    <Badge variant="secondary" className="ml-2">{emails.length}</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Account Filter */}
                <div className="mb-4">
                  <Select value={accountFilter || 'all'} onValueChange={(value) => setAccountFilter(value === 'all' ? '' : value)}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="All Accounts" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Accounts</SelectItem>
                      {/* Add account options here when available */}
                    </SelectContent>
                  </Select>
                </div>

                {emails.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    {selectedCategory ? 'No emails found in this category' : 'Select a category to view emails'}
                  </div>
                ) : (
                  <EmailList emails={emails} />
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
} 