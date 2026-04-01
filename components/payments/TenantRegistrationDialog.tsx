'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { formatPhoneNumber, isValidPhoneNumber } from '@/lib/payment-utils';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TenantData {
  id: string;
  name: string;
  mobile_number: string;
  email?: string;
  address?: string;
  phone?: string;
  clickpesa_enabled: boolean;
  created_at: string;
}

interface TenantRegistrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTenantCreated: (tenant: TenantData) => void;
}

export function TenantRegistrationDialog({
  open,
  onOpenChange,
  onTenantCreated,
}: TenantRegistrationDialogProps) {
  const [formStep, setFormStep] = useState<'basic' | 'confirm'>('basic');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mobileError, setMobileError] = useState('');
  const [confirmMobileNumber, setConfirmMobileNumber] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    mobile_number: '',
    email: '',
    address: '',
    phone: '',
  });

  const validateMobileNumber = (phone: string) => {
    const digitsOnly = phone.replace(/\D/g, '');

    if (digitsOnly.length < 9) {
      return 'Mobile number must have at least 9 digits';
    }

    if (!isValidPhoneNumber(phone)) {
      return 'Please enter a valid Tanzania mobile number (starting with +255 or 0)';
    }

    return '';
  };

  const handleMobileNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData({ ...formData, mobile_number: value });
    setMobileError(validateMobileNumber(value));
  };

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name) {
      toast.error('Please enter tenant name');
      return;
    }

    if (!formData.mobile_number) {
      toast.error('Please enter the mobile number that will receive payments');
      return;
    }

    const error = validateMobileNumber(formData.mobile_number);
    if (error) {
      setMobileError(error);
      toast.error(error);
      return;
    }

    setConfirmMobileNumber('');
    setFormStep('confirm');
  };

  const handleRegisterTenant = async (e: React.FormEvent) => {
    e.preventDefault();

    const normalizedMobileNumber = formatPhoneNumber(formData.mobile_number);
    const normalizedConfirmMobileNumber = formatPhoneNumber(confirmMobileNumber);

    if (normalizedMobileNumber !== normalizedConfirmMobileNumber) {
      toast.error('Mobile numbers do not match. Please re-enter to confirm.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${BASE_URL}/api/payments/clickpesa/tenants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          name: formData.name,
          mobile_number: normalizedMobileNumber,
          email: formData.email || undefined,
          phone: formData.phone || undefined,
          address: formData.address || undefined,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to register tenant');
      }

      const tenant: TenantData = await response.json();

      setFormStep('basic');
      setFormData({
        name: '',
        mobile_number: '',
        email: '',
        address: '',
        phone: '',
      });
      setConfirmMobileNumber('');
      setMobileError('');

      toast.success('✅ Tenant registered successfully!', {
        description: `${tenant.name} will receive payments on ${tenant.mobile_number}`,
      });

      onTenantCreated(tenant);
      onOpenChange(false);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Registration failed';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormStep('basic');
      setFormData({
        name: '',
        mobile_number: '',
        email: '',
        address: '',
        phone: '',
      });
      setConfirmMobileNumber('');
      setMobileError('');
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="rounded-2xl max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Register New Tenant</DialogTitle>
          <DialogDescription>
            {formStep === 'basic'
              ? 'Add a new restaurant/tenant to receive mobile money payments'
              : 'Confirm the mobile number that will receive all payments'}
          </DialogDescription>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {/* Step 1: Basic Information */}
          {formStep === 'basic' && (
            <motion.form
              key="basic"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              onSubmit={handleNextStep}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="name" className="font-semibold text-gray-900 dark:text-white">
                  Restaurant/Tenant Name *
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., Pizza Palace, The Grill House"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                  required
                />
              </div>

              {/* Mobile Number - PAYMENT WALLET */}
              <motion.div
                className="space-y-2 p-4 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-700"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="flex items-start gap-2">
                  <div className="w-6 h-6 rounded-full bg-amber-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-sm font-bold">💰</span>
                  </div>
                  <div className="flex-1">
                    <Label htmlFor="mobile" className="font-bold text-amber-900 dark:text-amber-100 block mb-2">
                      Payment Receiving Mobile Number *
                    </Label>
                    <Input
                      id="mobile"
                      type="tel"
                      placeholder="+255 755 XXX XXX"
                      value={formData.mobile_number}
                      onChange={handleMobileNumberChange}
                      className={`rounded-lg bg-white dark:bg-gray-900 border-2 transition-colors ${
                        mobileError
                          ? 'border-red-500 dark:border-red-500'
                          : formData.mobile_number && !mobileError
                          ? 'border-green-500 dark:border-green-500'
                          : 'border-amber-300 dark:border-amber-600'
                      }`}
                      required
                    />
                    <p className="text-xs text-amber-700 dark:text-amber-200 mt-2 font-medium">
                      ⚠️ This is the mobile money account that will receive ALL customer payments for this tenant
                    </p>
                    {mobileError && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-2 font-medium">
                        ❌ {mobileError}
                      </p>
                    )}
                    {formData.mobile_number && !mobileError && (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-2 font-medium">
                        ✅ Mobile number is valid
                      </p>
                    )}
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-3">
                      Format: +255 7XX XXX XXX or 07XX XXX XXX
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Optional Fields */}
              <div className="pt-2">
                <Label className="text-sm font-semibold text-gray-900 dark:text-white mb-3 block">
                  Additional Information (Optional)
                </Label>

                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm">
                      Email
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="restaurant@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="text-sm">
                      Contact Phone
                    </Label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+255 7XX XXX XXX"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="address" className="text-sm">
                      Address
                    </Label>
                    <Input
                      id="address"
                      placeholder="Business address"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      className="rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  className="flex-1 rounded-lg"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={!formData.name || !formData.mobile_number || !!mobileError || isSubmitting}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed text-white rounded-lg"
                >
                  {isSubmitting ? 'Processing...' : 'Next: Confirm →'}
                </Button>
              </div>
            </motion.form>
          )}

          {/* Step 2: Confirmation */}
          {formStep === 'confirm' && (
            <motion.form
              key="confirm"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              onSubmit={handleRegisterTenant}
              className="space-y-4"
            >
              {/* Summary Card */}
              <motion.div
                className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-700"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <p className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Review Information
                </p>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Tenant Name:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">{formData.name}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-blue-200 dark:border-blue-700">
                    <span className="text-gray-600 dark:text-gray-400">Payment Wallet:</span>
                    <span className="font-mono font-bold text-blue-600 dark:text-blue-300">{formData.mobile_number}</span>
                  </div>
                </div>
              </motion.div>

              {/* Confirmation Input */}
              <motion.div
                className="space-y-2 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border-2 border-red-300 dark:border-red-700"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <p className="text-sm font-bold text-red-900 dark:text-red-100 mb-3">
                  🔐 Critical: Re-enter the Payment Mobile Number to Confirm
                </p>
                <p className="text-xs text-red-800 dark:text-red-200 mb-3">
                  This ensures the correct mobile number is registered. Customers will send money to this number.
                </p>
                <Input
                  type="tel"
                  placeholder={formData.mobile_number}
                  value={confirmMobileNumber}
                  onChange={(e) => setConfirmMobileNumber(e.target.value)}
                  className={`rounded-lg bg-white dark:bg-gray-900 border-2 transition-colors ${
                    confirmMobileNumber && formatPhoneNumber(confirmMobileNumber) !== formatPhoneNumber(formData.mobile_number)
                      ? 'border-red-500 dark:border-red-500'
                      : confirmMobileNumber && formatPhoneNumber(confirmMobileNumber) === formatPhoneNumber(formData.mobile_number)
                      ? 'border-green-500 dark:border-green-500'
                      : 'border-red-300 dark:border-red-600'
                  }`}
                />
                {confirmMobileNumber && formatPhoneNumber(confirmMobileNumber) !== formatPhoneNumber(formData.mobile_number) && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2 font-medium">
                    ❌ Mobile numbers do not match
                  </p>
                )}
                {confirmMobileNumber !== '' && formatPhoneNumber(confirmMobileNumber) === formatPhoneNumber(formData.mobile_number) && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-2 font-medium">
                    ✅ Numbers match - Ready to register
                  </p>
                )}
              </motion.div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setFormStep('basic')}
                  className="flex-1 rounded-lg"
                  disabled={isSubmitting}
                >
                  ← Back
                </Button>
                <Button
                  type="submit"
                  disabled={formatPhoneNumber(confirmMobileNumber) !== formatPhoneNumber(formData.mobile_number) || isSubmitting}
                  className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed text-white rounded-lg font-bold"
                >
                  {isSubmitting ? 'Registering...' : '✓ Confirm & Register'}
                </Button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
