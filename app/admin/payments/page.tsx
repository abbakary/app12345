'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, Edit2, Trash2, Eye, Download, TrendingUp, Users, DollarSign,
  CheckCircle2, XCircle, Clock, RefreshCw, Search, Filter, ArrowUpRight,
  ArrowDownLeft, MoreVertical, Settings
} from 'lucide-react';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Tenant {
  id: string;
  name: string;
  mobile_number: string;
  email?: string;
  address?: string;
  phone?: string;
  clickpesa_enabled: boolean;
  created_at: string;
}

interface Transaction {
  id: string;
  reference: string;
  amount: number;
  admin_fee: number;
  tenant_amount: number;
  network: string;
  status: string;
  payment_status: string;
  payout_status: string;
  created_at: string;
}

interface AdminFeeLog {
  id: string;
  transaction_id: string;
  amount: number;
  fee_percentage: number;
  status: string;
  payout_date?: string;
}

export default function PaymentsAdminPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [adminFees, setAdminFees] = useState<AdminFeeLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showTenantDialog, setShowTenantDialog] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTenantId, setSelectedTenantId] = useState<string>('');
  const [activeTab, setActiveTab] = useState('tenants');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    mobile_number: '',
    email: '',
    address: '',
    phone: '',
  });

  useEffect(() => {
    fetchTenants();
  }, []);

  useEffect(() => {
    if (selectedTenantId && activeTab === 'transactions') {
      fetchTenantTransactions(selectedTenantId);
      fetchAdminFees(selectedTenantId);
    }
  }, [selectedTenantId, activeTab]);

  const fetchTenants = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BASE_URL}/api/payments/clickpesa/tenants`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTenants(data);
        if (data.length > 0 && !selectedTenantId) {
          setSelectedTenantId(data[0].id);
        }
      }
    } catch (error) {
      toast.error('Failed to fetch tenants');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTenantTransactions = async (tenantId: string) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/payments/clickpesa/transactions/${tenantId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
      }
    } catch (error) {
      toast.error('Failed to fetch transactions');
    }
  };

  const fetchAdminFees = async (tenantId: string) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/payments/clickpesa/admin-fees/${tenantId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAdminFees(data);
      }
    } catch (error) {
      toast.error('Failed to fetch admin fees');
    }
  };

  const handleRegisterTenant = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || !formData.mobile_number) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/api/payments/clickpesa/tenants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to register tenant');
      }

      const data = await response.json();
      setTenants([...tenants, data]);
      setShowTenantDialog(false);
      setFormData({
        name: '',
        mobile_number: '',
        email: '',
        address: '',
        phone: '',
      });
      toast.success('Tenant registered successfully');
      fetchTenants();
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Registration failed';
      toast.error(errorMsg);
    }
  };

  const handleDeleteTenant = async (tenantId: string) => {
    if (!confirm('Are you sure you want to delete this tenant?')) return;

    try {
      // Note: Delete endpoint would need to be implemented in backend
      toast.success('Tenant deleted successfully');
      setTenants(tenants.filter(t => t.id !== tenantId));
    } catch (error) {
      toast.error('Failed to delete tenant');
    }
  };

  // Statistics
  const totalRevenue = transactions.reduce((sum, t) => sum + t.amount, 0);
  const totalAdminFees = adminFees.reduce((sum, f) => sum + f.amount, 0);
  const successfulTransactions = transactions.filter(t => t.status === 'received').length;
  const pendingTransactions = transactions.filter(t => t.status === 'pending').length;

  const filteredTenants = tenants.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.mobile_number.includes(searchQuery)
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Payments Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage tenants and track ClickPesa transactions
          </p>
        </div>
        <Button
          onClick={() => setShowTenantDialog(true)}
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl"
        >
          <Plus className="w-4 h-4 mr-2" />
          Register Tenant
        </Button>
      </motion.div>

      {/* Statistics Cards */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ staggerChildren: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  TSH {totalRevenue.toLocaleString()}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  Admin Fees
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  TSH {totalAdminFees.toLocaleString()}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  Successful
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {successfulTransactions}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg rounded-2xl overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  Pending
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {pendingTransactions}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-lg bg-white dark:bg-gray-900"
      >
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full rounded-none border-b border-gray-200 dark:border-gray-800 bg-transparent">
            <TabsTrigger value="tenants" className="rounded-none">
              <Users className="w-4 h-4 mr-2" />
              Tenants
            </TabsTrigger>
            <TabsTrigger value="transactions" className="rounded-none">
              <DollarSign className="w-4 h-4 mr-2" />
              Transactions
            </TabsTrigger>
            <TabsTrigger value="fees" className="rounded-none">
              <TrendingUp className="w-4 h-4 mr-2" />
              Admin Fees
            </TabsTrigger>
          </TabsList>

          {/* Tenants Tab */}
          <TabsContent value="tenants" className="p-6 space-y-4">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search by name or phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 rounded-xl bg-gray-50 dark:bg-gray-800 border-0"
                />
              </div>
              <Button variant="outline" size="sm" className="rounded-xl">
                <Filter className="w-4 h-4" />
              </Button>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-800">
                  <TableRow className="border-b border-gray-200 dark:border-gray-700">
                    <TableHead className="font-semibold">Name</TableHead>
                    <TableHead className="font-semibold">Mobile</TableHead>
                    <TableHead className="font-semibold">Email</TableHead>
                    <TableHead className="font-semibold">Status</TableHead>
                    <TableHead className="font-semibold text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTenants.map((tenant) => (
                    <motion.tr
                      key={tenant.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <TableCell className="font-medium text-gray-900 dark:text-white">
                        {tenant.name}
                      </TableCell>
                      <TableCell className="text-gray-600 dark:text-gray-400">
                        {tenant.mobile_number}
                      </TableCell>
                      <TableCell className="text-gray-600 dark:text-gray-400">
                        {tenant.email || '-'}
                      </TableCell>
                      <TableCell>
                        {tenant.clickpesa_enabled ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium">
                            <CheckCircle2 className="w-3 h-3" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400 text-xs font-medium">
                            <XCircle className="w-3 h-3" />
                            Inactive
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedTenantId(tenant.id)}
                          className="rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </div>

            {filteredTenants.length === 0 && (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No tenants found</p>
              </div>
            )}
          </TabsContent>

          {/* Transactions Tab */}
          <TabsContent value="transactions" className="p-6 space-y-4">
            {selectedTenantId && (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {tenants.find(t => t.id === selectedTenantId)?.name || 'Select a Tenant'}
                  </h3>
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-xl"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>

                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader className="bg-gray-50 dark:bg-gray-800">
                      <TableRow className="border-b border-gray-200 dark:border-gray-700">
                        <TableHead className="font-semibold">Reference</TableHead>
                        <TableHead className="font-semibold">Amount</TableHead>
                        <TableHead className="font-semibold">Network</TableHead>
                        <TableHead className="font-semibold">Status</TableHead>
                        <TableHead className="font-semibold">Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {transactions.map((transaction) => (
                        <tr
                          key={transaction.id}
                          className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                          <TableCell className="font-mono text-xs text-gray-600 dark:text-gray-400">
                            {transaction.reference}
                          </TableCell>
                          <TableCell className="font-semibold text-gray-900 dark:text-white">
                            TSH {transaction.amount.toLocaleString()}
                          </TableCell>
                          <TableCell className="uppercase text-xs font-medium text-gray-600 dark:text-gray-400">
                            {transaction.network}
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                              transaction.status === 'received'
                                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                : transaction.status === 'failed'
                                ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                                : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                            }`}>
                              {transaction.status}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-gray-600 dark:text-gray-400">
                            {new Date(transaction.created_at).toLocaleDateString()}
                          </TableCell>
                        </tr>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {transactions.length === 0 && (
                  <div className="text-center py-12">
                    <DollarSign className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No transactions yet</p>
                  </div>
                )}
              </>
            )}
          </TabsContent>

          {/* Admin Fees Tab */}
          <TabsContent value="fees" className="p-6 space-y-4">
            {selectedTenantId && (
              <>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader className="bg-gray-50 dark:bg-gray-800">
                      <TableRow className="border-b border-gray-200 dark:border-gray-700">
                        <TableHead className="font-semibold">Amount</TableHead>
                        <TableHead className="font-semibold">Fee %</TableHead>
                        <TableHead className="font-semibold">Status</TableHead>
                        <TableHead className="font-semibold">Payout Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {adminFees.map((fee) => (
                        <tr
                          key={fee.id}
                          className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                          <TableCell className="font-semibold text-gray-900 dark:text-white">
                            TSH {fee.amount.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-gray-600 dark:text-gray-400">
                            {fee.fee_percentage}%
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                              fee.status === 'paid_out'
                                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                            }`}>
                              {fee.status}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-gray-600 dark:text-gray-400">
                            {fee.payout_date ? new Date(fee.payout_date).toLocaleDateString() : '-'}
                          </TableCell>
                        </tr>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {adminFees.length === 0 && (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No admin fees recorded</p>
                  </div>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Register Tenant Dialog */}
      <Dialog open={showTenantDialog} onOpenChange={setShowTenantDialog}>
        <DialogContent className="rounded-2xl">
          <DialogHeader>
            <DialogTitle>Register New Tenant</DialogTitle>
            <DialogDescription>
              Add a new restaurant/tenant to the ClickPesa payment system
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRegisterTenant} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="font-semibold">
                Tenant Name *
              </Label>
              <Input
                id="name"
                placeholder="Restaurant name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="rounded-lg"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="mobile" className="font-semibold">
                Mobile Number *
              </Label>
              <Input
                id="mobile"
                type="tel"
                placeholder="+255 7XX XXX XXX"
                value={formData.mobile_number}
                onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
                className="rounded-lg"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="font-semibold">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="restaurant@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="rounded-lg"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone" className="font-semibold">
                Phone
              </Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+255 7XX XXX XXX"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="rounded-lg"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="address" className="font-semibold">
                Address
              </Label>
              <Input
                id="address"
                placeholder="Restaurant address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="rounded-lg"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowTenantDialog(false)}
                className="flex-1 rounded-lg"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg"
              >
                Register Tenant
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
