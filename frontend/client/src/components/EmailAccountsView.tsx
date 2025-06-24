import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, 
  Mail, 
  Trash2, 
  RefreshCw, 
  Eye, 
  EyeOff,
  CheckCircle,
  XCircle,
  Calendar
} from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

const emailAccountSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
  imapHost: z.string().default("mail.hostinger.com"),
  imapPort: z.number().default(993),
  smtpHost: z.string().default("mail.hostinger.com"),
  smtpPort: z.number().default(465),
});

type EmailAccountForm = z.infer<typeof emailAccountSchema>;

interface EmailAccount {
  id: number;
  email: string;
  username: string;
  password: string;
  imapHost: string;
  imapPort: number;
  smtpHost: string;
  smtpPort: number;
  isActive: boolean;
  lastSync: string | null;
  createdAt: string;
}

export default function EmailAccountsView() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<number, boolean>>({});
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["/api/email-accounts"],
  });

  const form = useForm<EmailAccountForm>({
    resolver: zodResolver(emailAccountSchema),
    defaultValues: {
      email: "",
      username: "",
      password: "",
      imapHost: "mail.hostinger.com",
      imapPort: 993,
      smtpHost: "mail.hostinger.com",
      smtpPort: 465,
    },
  });

  const createAccountMutation = useMutation({
    mutationFn: (data: EmailAccountForm) => apiRequest("POST", "/api/email-accounts", data),
    onSuccess: () => {
      toast({
        title: "Email account added",
        description: "New email account has been successfully configured",
      });
      setIsDialogOpen(false);
      form.reset();
      queryClient.invalidateQueries({ queryKey: ["/api/email-accounts"] });
    },
    onError: () => {
      toast({
        title: "Failed to add account",
        description: "Please check your credentials and try again",
        variant: "destructive",
      });
    },
  });

  const syncEmailsMutation = useMutation({
    mutationFn: () => apiRequest("POST", "/api/emails/fetch"),
    onSuccess: () => {
      toast({
        title: "Email sync started",
        description: "Fetching emails from all configured accounts...",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/emails"] });
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"] });
    },
    onError: () => {
      toast({
        title: "Sync failed",
        description: "Failed to start email synchronization",
        variant: "destructive",
      });
    },
  });

  const toggleAccountMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => 
      apiRequest("PATCH", `/api/email-accounts/${id}`, { isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/email-accounts"] });
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: (id: number) => apiRequest("DELETE", `/api/email-accounts/${id}`),
    onSuccess: () => {
      toast({
        title: "Account deleted",
        description: "Email account has been removed",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/email-accounts"] });
    },
  });

  const onSubmit = async (data: EmailAccountForm) => {
    createAccountMutation.mutate(data);
  };

  const togglePasswordVisibility = (accountId: number) => {
    setShowPasswords(prev => ({
      ...prev,
      [accountId]: !prev[accountId]
    }));
  };

  const formatLastSync = (date: string | null) => {
    if (!date) return "Never";
    return new Date(date).toLocaleString();
  };

  const accountsList = Array.isArray(accounts) ? accounts as EmailAccount[] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-800">Email Accounts</h2>
          <p className="text-gray-600">Manage your Hostinger email accounts for automated fetching</p>
        </div>
        
        <div className="flex space-x-3">
          <Button
            onClick={() => syncEmailsMutation.mutate()}
            disabled={syncEmailsMutation.isPending}
            className="bg-secondary hover:bg-emerald-700 text-white"
          >
            {syncEmailsMutation.isPending ? (
              <RefreshCw className="mr-2 w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 w-4 h-4" />
            )}
            Sync All Emails
          </Button>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-primary hover:bg-blue-700 text-white">
                <Plus className="mr-2 w-4 h-4" />
                Add Email Account
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add New Email Account</DialogTitle>
              </DialogHeader>
              
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email Address</FormLabel>
                          <FormControl>
                            <Input placeholder="support@yourdomain.com" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="username"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Username</FormLabel>
                          <FormControl>
                            <Input placeholder="Usually same as email" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="Email account password" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <Separator />
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-4">
                      <h4 className="font-medium text-sm text-gray-700">IMAP Settings</h4>
                      <FormField
                        control={form.control}
                        name="imapHost"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>IMAP Host</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="imapPort"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>IMAP Port</FormLabel>
                            <FormControl>
                              <Input 
                                type="number" 
                                {...field} 
                                onChange={(e) => field.onChange(parseInt(e.target.value))}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    <div className="space-y-4">
                      <h4 className="font-medium text-sm text-gray-700">SMTP Settings</h4>
                      <FormField
                        control={form.control}
                        name="smtpHost"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>SMTP Host</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="smtpPort"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>SMTP Port</FormLabel>
                            <FormControl>
                              <Input 
                                type="number" 
                                {...field} 
                                onChange={(e) => field.onChange(parseInt(e.target.value))}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setIsDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button 
                      type="submit" 
                      disabled={createAccountMutation.isPending}
                      className="bg-primary hover:bg-blue-700 text-white"
                    >
                      {createAccountMutation.isPending ? "Adding..." : "Add Account"}
                    </Button>
                  </div>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Accounts List */}
      <Card>
        <CardHeader>
          <CardTitle>Configured Email Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              <p className="text-gray-500">Loading email accounts...</p>
            </div>
          ) : accountsList.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email Account</TableHead>
                  <TableHead>Server Settings</TableHead>
                  <TableHead>Credentials</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accountsList.map((account: EmailAccount) => (
                  <TableRow key={account.id}>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Mail className="w-4 h-4 text-blue-500" />
                        <div>
                          <p className="font-medium">{account.email}</p>
                          <p className="text-xs text-gray-500">ID: {account.id}</p>
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div>IMAP: {account.imapHost}:{account.imapPort}</div>
                        <div>SMTP: {account.smtpHost}:{account.smtpPort}</div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div>User: {account.username}</div>
                        <div className="flex items-center space-x-2">
                          <span>Pass: </span>
                          {showPasswords[account.id] ? (
                            <span className="font-mono text-xs">{account.password}</span>
                          ) : (
                            <span className="font-mono text-xs">••••••••</span>
                          )}
                          <Button
                            size="icon"
                            variant="ghost"
                            className="w-4 h-4"
                            onClick={() => togglePasswordVisibility(account.id)}
                          >
                            {showPasswords[account.id] ? (
                              <EyeOff className="w-3 h-3" />
                            ) : (
                              <Eye className="w-3 h-3" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {account.isActive ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-800">
                            <XCircle className="w-3 h-3 mr-1" />
                            Inactive
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center space-x-2 text-sm">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span>{formatLastSync(account.lastSync)}</span>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={account.isActive}
                          onCheckedChange={(checked) => 
                            toggleAccountMutation.mutate({ id: account.id, isActive: checked })
                          }
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => deleteAccountMutation.mutate(account.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No email accounts configured</h3>
              <p className="text-gray-500 mb-4">
                Add your first Hostinger email account to start fetching emails automatically
              </p>
              <Button onClick={() => setIsDialogOpen(true)} className="bg-primary hover:bg-blue-700 text-white">
                <Plus className="mr-2 w-4 h-4" />
                Add Email Account
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}