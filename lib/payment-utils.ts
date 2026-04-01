/**
 * Payment utilities for ClickPesa integration
 * Handles payment flow, session management, and API calls
 */

interface PaymentSession {
  amount: number;
  tenant_id: string;
  tenant_name: string;
  order_reference: string;
}

/**
 * Initiate payment flow after order placement
 */
export const initiatePaymentFlow = (paymentData: PaymentSession) => {
  // Store payment session
  sessionStorage.setItem('pendingPayment', JSON.stringify(paymentData));
  
  // Redirect to payment page
  window.location.href = '/customer/payments';
};

/**
 * Clear payment session
 */
export const clearPaymentSession = () => {
  sessionStorage.removeItem('pendingPayment');
};

/**
 * Get payment session from storage
 */
export const getPaymentSession = (): PaymentSession | null => {
  try {
    const session = sessionStorage.getItem('pendingPayment');
    return session ? JSON.parse(session) : null;
  } catch {
    return null;
  }
};

/**
 * Create payment instance with ClickPesa
 */
export const createClickPesaPayment = async (
  amount: number,
  network: string,
  customerPhone: string,
  tenantId: string,
  orderReference?: string
) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${baseUrl}/api/payments/clickpesa/initiate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        amount,
        network: network.toLowerCase(),
        customer_phone: customerPhone,
        tenant_id: tenantId,
        order_reference: orderReference,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Payment initiation failed');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Get payment status
 */
export const getPaymentStatus = async (reference: string) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    const response = await fetch(
      `${baseUrl}/api/payments/clickpesa/transactions/status/${reference}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch payment status');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Format phone number for display
 */
export const normalizeTanzaniaPhoneNumber = (phone: string): string | null => {
  const cleaned = phone.replace(/[^\d+]/g, '');
  const digitsOnly = cleaned.replace(/\D/g, '');

  let localNumber = digitsOnly;

  if (cleaned.startsWith('+')) {
    if (!cleaned.startsWith('+255')) {
      return null;
    }
    localNumber = digitsOnly.slice(3);
  } else if (digitsOnly.startsWith('255')) {
    localNumber = digitsOnly.slice(3);
  } else if (digitsOnly.startsWith('0')) {
    localNumber = digitsOnly.slice(1);
  }

  if (!/^[67]\d{8}$/.test(localNumber)) {
    return null;
  }

  return `+255${localNumber}`;
};

export const formatPhoneNumber = (phone: string): string => {
  return normalizeTanzaniaPhoneNumber(phone) || phone;
};

/**
 * Validate phone number
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  return normalizeTanzaniaPhoneNumber(phone) !== null;
};

/**
 * Get network from phone number (based on first digits)
 */
export const detectNetworkFromPhone = (phone: string): string | null => {
  const digitsOnly = phone.replace(/\D/g, '');
  
  if (digitsOnly.length < 3) return null;

  // Tanzania mobile network prefixes
  // Airtel: 68, 69
  // Tigo: 65, 67, 71, 72, 73, 74, 75, 76
  // Halotel: 62, 63, 64
  
  const prefix = digitsOnly.slice(-10, -8);
  
  if (['68', '69'].includes(prefix)) return 'airtel';
  if (['65', '67', '71', '72', '73', '74', '75', '76'].includes(prefix)) return 'tigo';
  if (['62', '63', '64'].includes(prefix)) return 'halotel';
  
  return null;
};

/**
 * Calculate admin fee
 */
export const calculateAdminFee = (amount: number, feePercentage: number = 10): number => {
  return (amount * feePercentage) / 100;
};

/**
 * Calculate tenant amount
 */
export const calculateTenantAmount = (amount: number, feePercentage: number = 10): number => {
  return amount - calculateAdminFee(amount, feePercentage);
};
