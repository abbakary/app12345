'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Check, X, Clock, Smartphone, Lock, Phone, ChevronRight,
  AlertCircle, Repeat2, Home
} from 'lucide-react';
import Link from 'next/link';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mobile network logos/colors
const NETWORKS = [
  {
    id: 'airtel',
    name: 'Airtel',
    color: 'from-red-600 to-red-700',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-700',
    textColor: 'text-red-700 dark:text-red-300',
    icon: '📱', // Using emoji as logo
  },
  {
    id: 'tigo',
    name: 'Tigo/Yas',
    color: 'from-purple-600 to-purple-700',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    borderColor: 'border-purple-200 dark:border-purple-700',
    textColor: 'text-purple-700 dark:text-purple-300',
    icon: '💜',
  },
  {
    id: 'halotel',
    name: 'Halotel',
    color: 'from-blue-600 to-blue-700',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-700',
    textColor: 'text-blue-700 dark:text-blue-300',
    icon: '🔵',
  },
];

type PaymentStep = 'method-selection' | 'phone-input' | 'processing' | 'success' | 'failed';

interface PaymentState {
  amount: number;
  tenant_id: string;
  tenant_name: string;
  order_reference: string;
}

export default function PaymentPage() {
  const [step, setStep] = useState<PaymentStep>('method-selection');
  const [selectedNetwork, setSelectedNetwork] = useState<string>('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentState, setPaymentState] = useState<PaymentState | null>(null);
  const [transactionReference, setTransactionReference] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);

  // Load payment context from session/order
  useEffect(() => {
    const sessionPayment = sessionStorage.getItem('pendingPayment');
    if (sessionPayment) {
      try {
        const payment = JSON.parse(sessionPayment);
        setPaymentState(payment);
      } catch {
        toast.error('Invalid payment session');
      }
    }
  }, []);

  const handleNetworkSelect = (networkId: string) => {
    setSelectedNetwork(networkId);
    setShowConfirmation(false);
  };

  const handlePhoneInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Only allow digits and + symbol
    const value = e.target.value.replace(/[^\d+]/g, '');
    setCustomerPhone(value);
  };

  const validatePhoneNumber = () => {
    // Basic validation: at least 9 digits
    const digitsOnly = customerPhone.replace(/\D/g, '');
    return digitsOnly.length >= 9;
  };

  const handleInitiatePayment = async () => {
    if (!selectedNetwork) {
      toast.error('Please select a payment method');
      return;
    }

    if (!customerPhone) {
      toast.error('Please enter your phone number');
      return;
    }

    if (!validatePhoneNumber()) {
      toast.error('Please enter a valid phone number (at least 9 digits)');
      return;
    }

    if (!paymentState) {
      toast.error('Payment information not found');
      return;
    }

    setShowConfirmation(true);
  };

  const confirmPayment = async () => {
    if (!paymentState) return;

    setIsProcessing(true);
    setStep('processing');

    try {
      const response = await fetch(`${BASE_URL}/api/payments/clickpesa/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: paymentState.amount,
          network: selectedNetwork.toLowerCase(),
          customer_phone: customerPhone,
          tenant_id: paymentState.tenant_id,
          order_reference: paymentState.order_reference,
          additional_data: {
            tenant_name: paymentState.tenant_name,
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Payment initiation failed');
      }

      const data = await response.json();
      setTransactionReference(data.reference);

      // Simulate payment processing delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      setStep('success');
      toast.success('Payment initiated successfully!');

      // Clear session
      sessionStorage.removeItem('pendingPayment');

      // Redirect after 3 seconds
      setTimeout(() => {
        window.location.href = '/customer/orders';
      }, 3000);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Payment failed';
      setErrorMessage(errorMsg);
      setStep('failed');
      toast.error(errorMsg);
    } finally {
      setIsProcessing(false);
      setShowConfirmation(false);
    }
  };

  if (!paymentState) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md text-center"
        >
          <Card className="border-0 shadow-2xl rounded-3xl">
            <CardContent className="pt-12 pb-12">
              <AlertCircle className="w-16 h-16 mx-auto text-amber-500 mb-4" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                No Payment Session
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Please complete your order first to proceed with payment.
              </p>
              <Link href="/customer">
                <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl">
                  <Home className="w-4 h-4 mr-2" />
                  Back to Menu
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <Link href="/customer">
            <Button variant="ghost" size="sm" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>

          <Card className="border-0 shadow-lg rounded-3xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white overflow-hidden">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium opacity-90">Amount to Pay</span>
                <Lock className="w-4 h-4 opacity-70" />
              </div>
              <h1 className="text-4xl font-bold mb-2">
                TSH {paymentState.amount.toLocaleString()}
              </h1>
              <p className="text-white/80 text-sm">
                {paymentState.tenant_name}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Payment Steps */}
        <AnimatePresence mode="wait">
          {/* Step 1: Network Selection */}
          {step === 'method-selection' && (
            <motion.div
              key="method-selection"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <Card className="border-0 shadow-lg rounded-3xl">
                <CardHeader className="pb-4">
                  <CardTitle>Select Payment Method</CardTitle>
                  <CardDescription>
                    Choose your mobile money network
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {NETWORKS.map((network, index) => (
                    <motion.button
                      key={network.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => handleNetworkSelect(network.id)}
                      className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
                        selectedNetwork === network.id
                          ? `bg-gradient-to-r ${network.color} text-white border-transparent shadow-lg`
                          : `${network.bgColor} ${network.borderColor} border-2 hover:border-current`
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{network.icon}</span>
                          <div>
                            <p className="font-bold">{network.name}</p>
                            <p className="text-xs opacity-70">Mobile Money</p>
                          </div>
                        </div>
                        {selectedNetwork === network.id && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-6 h-6 bg-white rounded-full flex items-center justify-center"
                          >
                            <Check className="w-4 h-4 text-green-600" />
                          </motion.div>
                        )}
                      </div>
                    </motion.button>
                  ))}
                </CardContent>
              </Card>

              {/* Step 2: Phone Number Input */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Card className="border-0 shadow-lg rounded-3xl">
                  <CardHeader className="pb-4">
                    <CardTitle>Your Phone Number</CardTitle>
                    <CardDescription>
                      Enter the mobile number for payment confirmation
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="font-semibold">
                        Mobile Number
                      </Label>
                      <div className="relative">
                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input
                          id="phone"
                          type="tel"
                          placeholder="+255 7XX XXX XXX"
                          value={customerPhone}
                          onChange={handlePhoneInputChange}
                          className="pl-12 rounded-xl bg-white/80 dark:bg-gray-900/80 border-gray-200 dark:border-gray-700"
                        />
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        Include country code (e.g., +255 for Tanzania)
                      </p>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleInitiatePayment}
                      disabled={!selectedNetwork || !customerPhone}
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-all shadow-lg"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <Smartphone className="w-5 h-5" />
                        Continue to Payment
                        <ChevronRight className="w-5 h-5" />
                      </div>
                    </motion.button>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Security Info */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-blue-50 dark:bg-blue-900/30 rounded-2xl p-4 flex gap-3"
              >
                <Lock className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
                    Secure Payment
                  </p>
                  <p className="text-xs text-blue-700 dark:text-blue-400">
                    All transactions are encrypted and secure with HMAC SHA256 verification
                  </p>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* Step 2: Confirmation */}
          {showConfirmation && (
            <motion.div
              key="confirmation"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 bg-black/50 flex items-end z-50"
            >
              <motion.div
                initial={{ y: 100 }}
                animate={{ y: 0 }}
                exit={{ y: 100 }}
                className="w-full bg-white dark:bg-gray-900 rounded-3xl rounded-b-none p-6 space-y-4"
              >
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  Confirm Payment
                </h3>

                <div className="bg-gray-50 dark:bg-gray-800 rounded-2xl p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Network</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {NETWORKS.find(n => n.id === selectedNetwork)?.name}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Phone</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {customerPhone}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span className="text-gray-600 dark:text-gray-400">Amount</span>
                    <span className="font-bold text-lg text-blue-600 dark:text-blue-400">
                      TSH {paymentState.amount.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowConfirmation(false)}
                    className="flex-1 rounded-xl"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={confirmPayment}
                    disabled={isProcessing}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl"
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Processing...
                      </div>
                    ) : (
                      <>
                        Confirm
                        <ChevronRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* Step 3: Processing */}
          {step === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <Card className="border-0 shadow-lg rounded-3xl">
                <CardContent className="pt-12 pb-12 text-center space-y-4">
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Clock className="w-16 h-16 mx-auto text-blue-600 dark:text-blue-400" />
                  </motion.div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Processing Payment
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Please confirm the payment on your phone
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 italic">
                    Do not close this page
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 4: Success */}
          {step === 'success' && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="space-y-4"
            >
              <Card className="border-0 shadow-lg rounded-3xl overflow-hidden bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30">
                <CardContent className="pt-12 pb-12 text-center space-y-4">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: 'spring' }}
                    className="w-20 h-20 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto"
                  >
                    <Check className="w-10 h-10 text-white" />
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                      Payment Successful!
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      Your payment has been confirmed
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-white dark:bg-gray-900 rounded-2xl p-4 space-y-2 text-left"
                  >
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Transaction ID</span>
                      <span className="font-mono text-xs text-gray-900 dark:text-white">
                        {transactionReference}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Amount Paid</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        TSH {paymentState.amount.toLocaleString()}
                      </span>
                    </div>
                  </motion.div>

                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    Redirecting to your orders...
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Step 5: Failed */}
          {step === 'failed' && (
            <motion.div
              key="failed"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="space-y-4"
            >
              <Card className="border-0 shadow-lg rounded-3xl overflow-hidden bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/30 dark:to-orange-900/30">
                <CardContent className="pt-12 pb-12 text-center space-y-4">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: 'spring' }}
                    className="w-20 h-20 bg-gradient-to-r from-red-400 to-orange-500 rounded-full flex items-center justify-center mx-auto"
                  >
                    <X className="w-10 h-10 text-white" />
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
                      Payment Failed
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      {errorMessage || 'Unable to process your payment'}
                    </p>
                  </motion.div>

                  <div className="flex gap-3 pt-2">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setStep('method-selection');
                        setShowConfirmation(false);
                        setIsProcessing(false);
                      }}
                      className="flex-1 rounded-xl"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        setStep('method-selection');
                        setSelectedNetwork('');
                        setCustomerPhone('');
                        setErrorMessage('');
                      }}
                      className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl"
                    >
                      <Repeat2 className="w-4 h-4 mr-2" />
                      Try Again
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
