'use client';

import { useState } from 'react';
import { usePayments, useOrders } from '@/hooks/use-restaurant-data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { ReceiptDialog } from '@/components/reception/receipt-dialog';
import { TenantRegistrationDialog } from '@/components/payments/TenantRegistrationDialog';
import { Button } from '@/components/ui/button';
import { Receipt, CreditCard, Banknote, Smartphone, QrCode, Plus } from 'lucide-react';
import type { Order } from '@/lib/types';

const methodIcons = {
  cash: Banknote,
  card: CreditCard,
  mobile: Smartphone,
  qr: QrCode,
};

export default function PaymentsPage() {
  const { data: payments = [], isLoading: paymentsLoading } = usePayments();
  const { data: orders = [], isLoading: ordersLoading } = useOrders();
  const [selectedOrder, setSelectedOrder] = useState<{order: Order, method: string} | null>(null);
  const [showTenantDialog, setShowTenantDialog] = useState(false);

  if (paymentsLoading || ordersLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Payments</h1>
          <p className="text-muted-foreground">View all completed payments</p>
        </div>
        <Button
          onClick={() => setShowTenantDialog(true)}
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 rounded-lg"
        >
          <Plus className="w-4 h-4 mr-2" />
          Register Tenant for Mobile Money
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {payments.map((payment) => {
          const order = orders.find(o => o.id === payment.orderId);
          const Icon = methodIcons[payment.method as keyof typeof methodIcons] || Banknote;

          return (
            <Card key={payment.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">${payment.amount.toFixed(2)}</CardTitle>
                      <p className="text-xs text-muted-foreground capitalize">
                        {payment.method}
                      </p>
                    </div>
                  </div>
                  <Badge variant="default" className="bg-green-500">
                    {payment.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between text-muted-foreground">
                    <span>Date</span>
                    <span>{format(new Date(payment.createdAt), 'MMM dd, HH:mm')}</span>
                  </div>
                  <div className="flex justify-between text-muted-foreground">
                    <span>Order ID</span>
                    <span className="font-mono">#{payment.orderId.slice(-8).toUpperCase()}</span>
                  </div>
                  {order && (
                    <div className="flex justify-between text-muted-foreground">
                      <span>Table</span>
                      <span>{order.tableName}</span>
                    </div>
                  )}

                  {order && (
                    <Button 
                      variant="outline" 
                      className="w-full mt-4" 
                      onClick={() => setSelectedOrder({ order, method: payment.method })}
                    >
                      <Receipt className="h-4 w-4 mr-2" />
                      View Receipt
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}

        {payments.length === 0 && (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            No payments found.
          </div>
        )}
      </div>

      {selectedOrder && (
        <ReceiptDialog
          order={selectedOrder.order}
          paymentMethod={selectedOrder.method as any}
          open={!!selectedOrder}
          onOpenChange={(open) => !open && setSelectedOrder(null)}
        />
      )}

      <TenantRegistrationDialog
        open={showTenantDialog}
        onOpenChange={setShowTenantDialog}
        onTenantCreated={() => undefined}
      />
    </div>
  );
}
