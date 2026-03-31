# ClickPesa Multi-Tenant Payment System

A secure, production-ready payment system built with FastAPI (backend) and Next.js/React (frontend), integrated with ClickPesa for mobile money payments.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│  Customer Payment UI    │    Admin Dashboard     │    Order Page │
│  - Network Selection    │ - Tenant Registration  │ - Place Order │
│  - Phone Entry          │ - Transaction History  │ - Track Order │
│  - Payment Status       │ - Admin Fee Logs       │   with Payment│
└────────────────┬────────────────────────────────────┬────────────┘
                 │                                    │
                 │   HTTP REST API (Port 8000)       │
                 ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  Payment Endpoints                                              │
│  - POST /api/payments/clickpesa/initiate                        │
│  - POST /api/payments/clickpesa/webhook                         │
│  - GET /api/payments/clickpesa/transactions/{tenant_id}         │
│  - GET /api/payments/clickpesa/admin-fees/{tenant_id}           │
│  - GET /api/payments/clickpesa/dashboard/{tenant_id}            │
│                                                                  │
│  Tenant Management                                              │
│  - POST /api/payments/clickpesa/tenants                         │
│  - GET /api/payments/clickpesa/tenants                          │
│  - GET /api/payments/clickpesa/tenants/{tenant_id}              │
│  - PUT /api/payments/clickpesa/tenants/{tenant_id}              │
└────────────┬──────────────────────────────────┬─────────────────┘
             │                                  │
             │   HMAC SHA256 Verification       │
             ▼                                  ▼
┌────────────────────────┐         ┌──────────────────────────┐
│   ClickPesa API         │         │    MySQL Database        │
│ - Payment Initiation    │         │ - Tenants (Restaurant)   │
│ - Webhook Events        │         │ - Transactions           │
│ - Payout Management     │         │ - Admin Fee Logs         │
└────────────────────────┘         └──────────────────────────┘
```

## Database Models

### 1. Restaurant (Extended for ClickPesa)
```
- id: UUID (Primary Key)
- name: String
- email: String (optional)
- phone: String (optional)
- address: String (optional)
- clickpesa_mobile_number: String (Tenant's mobile to receive payments)
- clickpesa_enabled: Boolean (default: False)
- created_at: DateTime
```

### 2. ClickPesaTransaction
```
- id: UUID (Primary Key)
- tenant_id: FK (Restaurant)
- reference: String (Unique, indexed)
- amount: Float (Full transaction amount)
- admin_fee: Float (Platform fee - 10% by default)
- tenant_amount: Float (Amount for tenant)
- network: String (airtel, tigo, halotel)
- customer_phone: String
- tenant_mobile: String
- status: String (pending, processing, received, failed)
- payment_status: String (initiated, confirmed, failed)
- payout_status: String (pending, initiated, completed, failed, reversed)
- clickpesa_transaction_id: String (ClickPesa reference)
- webhook_events: JSON (Audit trail of webhook calls)
- metadata: JSON (Custom data)
- created_at: DateTime
- updated_at: DateTime
- webhook_processed_at: DateTime (Prevents duplicate processing)
```

### 3. AdminFeeLog
```
- id: UUID (Primary Key)
- transaction_id: FK (ClickPesaTransaction)
- amount: Float (Fee amount)
- fee_percentage: Float (Percentage used - default 10%)
- status: String (collected, pending_payout, paid_out)
- payout_id: String (Reference to payout transaction)
- payout_date: DateTime
- notes: String (optional)
- created_at: DateTime
- updated_at: DateTime
```

## Environment Variables

### Backend (.env)
```bash
# ClickPesa Configuration
CLICKPESA_API_KEY=SKQ2ci9HDbJYBJvLLgvSIFn1SLHDdwtYieudHUwNJT
CLICKPESA_CHECKSUM=CHKnCyqOqqOa4QApStaF6wdJTp6n2YFCZR0
CLICKPESA_BASE_URL=https://api.clickpesa.com
CLICKPESA_WEBHOOK_URL=https://lophophoral-laurine-immortalisable.ngrok-free.dev/api/payments/clickpesa/webhook

# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@localhost/database

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Server Configuration
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## API Endpoints

### Payment Endpoints

#### 1. Initiate Payment
```
POST /api/payments/clickpesa/initiate
Content-Type: application/json

Request Body:
{
  "amount": 50000,
  "network": "airtel",
  "customer_phone": "+255 7XX XXX XXX",
  "tenant_id": "restaurant-uuid",
  "order_reference": "ORD-123456",
  "metadata": {...}
}

Response:
{
  "id": "transaction-uuid",
  "reference": "clickpesa_abc123def456",
  "amount": 50000,
  "admin_fee": 5000,
  "tenant_amount": 45000,
  "network": "airtel",
  "customer_phone": "+255 7XX XXX XXX",
  "status": "processing",
  "payment_status": "initiated",
  "created_at": "2024-03-15T10:30:00Z"
}
```

#### 2. Webhook Callback
```
POST /api/payments/clickpesa/webhook
Headers:
  X-Checksum: <HMAC-SHA256 Checksum>

Request Body:
{
  "event": "payment_received|payment_failed|payout_initiated|...",
  "transaction_id": "clickpesa_abc123def456",
  "reference": "clickpesa_abc123def456",
  "amount": 50000,
  "network": "airtel",
  "status": "SUCCESS|FAILED",
  "timestamp": "2024-03-15T10:35:00Z",
  "checksum": "..."
}

Response:
{
  "status": "processed"
}
```

#### 3. Get Transaction Status
```
GET /api/payments/clickpesa/transactions/status/{reference}

Response:
{
  "id": "transaction-uuid",
  "reference": "clickpesa_abc123def456",
  "amount": 50000,
  "status": "received",
  "payment_status": "confirmed",
  "payout_status": "initiated",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:35:00Z"
}
```

#### 4. Get Tenant Transactions
```
GET /api/payments/clickpesa/transactions/{tenant_id}?skip=0&limit=100

Response:
[
  {
    "id": "transaction-uuid",
    "reference": "clickpesa_abc123def456",
    "amount": 50000,
    ...
  }
]
```

#### 5. Get Admin Fees
```
GET /api/payments/clickpesa/admin-fees/{tenant_id}?skip=0&limit=100

Response:
[
  {
    "id": "fee-uuid",
    "transaction_id": "transaction-uuid",
    "amount": 5000,
    "fee_percentage": 10.0,
    "status": "collected",
    "payout_date": null,
    "created_at": "2024-03-15T10:35:00Z"
  }
]
```

#### 6. Tenant Dashboard
```
GET /api/payments/clickpesa/dashboard/{tenant_id}

Response:
{
  "total_revenue": 450000,
  "total_admin_fees": 50000,
  "transactions_count": 10,
  "pending_count": 2,
  "successful_count": 7,
  "failed_count": 1
}
```

### Tenant Management Endpoints

#### 1. Register Tenant
```
POST /api/payments/clickpesa/tenants
Content-Type: application/json

Request Body:
{
  "name": "Restaurant Name",
  "mobile_number": "+255 7XX XXX XXX",
  "email": "restaurant@example.com",
  "address": "123 Main St",
  "phone": "+255 7XX XXX XXX",
  "metadata": {...}
}

Response:
{
  "id": "tenant-uuid",
  "name": "Restaurant Name",
  "mobile_number": "+255 7XX XXX XXX",
  "email": "restaurant@example.com",
  "address": "123 Main St",
  "phone": "+255 7XX XXX XXX",
  "clickpesa_enabled": true,
  "created_at": "2024-03-15T10:00:00Z"
}
```

#### 2. List Tenants
```
GET /api/payments/clickpesa/tenants?skip=0&limit=100

Response:
[
  {
    "id": "tenant-uuid",
    "name": "Restaurant Name",
    ...
  }
]
```

#### 3. Get Tenant
```
GET /api/payments/clickpesa/tenants/{tenant_id}

Response:
{
  "id": "tenant-uuid",
  "name": "Restaurant Name",
  ...
}
```

#### 4. Update Tenant
```
PUT /api/payments/clickpesa/tenants/{tenant_id}
Content-Type: application/json

Request Body:
{
  "name": "New Name",
  "mobile_number": "+255 7XX XXX XXX",
  "email": "new@example.com",
  "clickpesa_enabled": true
}

Response:
{
  "id": "tenant-uuid",
  "name": "New Name",
  ...
}
```

## Security Features

### 1. Webhook Verification
- All webhooks are verified using HMAC SHA256
- Uses the `CLICKPESA_CHECKSUM` secret key
- Prevents unauthorized webhook processing
- Constant-time comparison prevents timing attacks

```python
def verify_webhook_checksum(payload: str, provided_checksum: str) -> bool:
    calculated_checksum = hmac.new(
        checksum_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(calculated_checksum, provided_checksum)
```

### 2. Duplicate Prevention
- Transaction references are unique and indexed
- Webhook events are logged with timestamps
- Idempotency key (`webhook_processed_at`) prevents re-processing
- Safe for webhook retries

### 3. Multi-Tenant Isolation
- Each transaction is tied to a specific tenant
- Tenants can only view their own transactions
- Admin fees are tracked separately per transaction
- Data isolation enforced at database level

### 4. Secret Management
- API keys stored in environment variables
- Sensitive data never logged
- Checksum keys protected with HMAC verification
- HTTPS/TLS for all API communications

## Payment Flow

### Step 1: Customer Places Order
1. Customer selects items from menu
2. Chooses order type (dine-in, delivery, pickup)
3. Clicks "Place Order"
4. Order is created in database with status "pending"

### Step 2: Initiate Payment
```javascript
// Frontend redirects to payment page with session
sessionStorage.setItem('pendingPayment', {
  amount: 50000,
  tenant_id: "restaurant-uuid",
  tenant_name: "Restaurant Name",
  order_reference: "ORD-123456"
});
window.location.href = '/customer/payments';
```

### Step 3: Customer Selects Network & Phone
1. Customer selects payment network (Airtel, Tigo, Halotel)
2. Customer enters their phone number
3. Customer confirms payment

### Step 4: Backend Initiates Payment
1. Frontend sends payment request to backend
2. Backend validates input
3. Backend creates `ClickPesaTransaction` record
4. Backend calls ClickPesa API
5. ClickPesa returns transaction ID
6. Frontend shows "Processing" screen

### Step 5: Customer Confirms on Phone
1. Customer receives USSD prompt on their phone
2. Customer enters PIN to confirm payment
3. Mobile network processes payment
4. ClickPesa receives payment notification

### Step 6: Webhook Notification
1. ClickPesa sends webhook to backend
2. Backend verifies HMAC signature
3. Backend processes webhook event
4. Backend updates transaction status
5. Backend records admin fee
6. Frontend receives status update
7. Frontend redirects to orders page

## Testing the System

### 1. Test Environment Setup
```bash
# Start backend
cd backend
pip install -r requirements.txt
python main.py

# Start frontend (in another terminal)
cd ..
npm run dev

# Backend runs on http://localhost:8000
# Frontend runs on http://localhost:3000
```

### 2. Register a Test Tenant
1. Go to http://localhost:3000/admin/payments
2. Click "Register Tenant"
3. Fill in:
   - Name: "Test Restaurant"
   - Mobile: "+255 7XX XXX XXX"
   - Email: "test@restaurant.com"
4. Click "Register Tenant"

### 3. Test Payment Flow
1. Go to http://localhost:3000/customer
2. Place an order (add items to cart, click "Place Order")
3. Go through the order placement form
4. After order is placed, you'll be redirected to payment page
5. Select a network (Airtel, Tigo, or Halotel)
6. Enter your phone number
7. Click "Continue to Payment"
8. Confirm payment
9. Payment will show "Processing" then "Success" (mock)

### 4. Test Webhook Verification
```bash
# Send a test webhook to backend
curl -X POST http://localhost:8000/api/payments/clickpesa/webhook \
  -H "Content-Type: application/json" \
  -H "X-Checksum: <VALID_CHECKSUM>" \
  -d '{
    "event": "payment_received",
    "transaction_id": "clickpesa_test",
    "reference": "clickpesa_abc123",
    "amount": 50000,
    "network": "airtel",
    "status": "SUCCESS",
    "timestamp": "2024-03-15T10:35:00Z"
  }'
```

### 5. View Admin Dashboard
1. Go to http://localhost:3000/admin/payments
2. View statistics
3. Switch tabs to see:
   - Tenants list
   - Transaction history
   - Admin fee logs

## Mobile Network Detection

The system can automatically detect the mobile network from the customer's phone number:

```
Airtel: Prefixes 68, 69
Tigo/Yas: Prefixes 65, 67, 71, 72, 73, 74, 75, 76
Halotel: Prefixes 62, 63, 64
```

Example:
- +255 6XX XXX XXX → Airtel
- +255 7X XXX XXX → Tigo/Yas (if prefix matches)
- +255 6XX XXX XXX → Halotel (if prefix matches)

## Fee Structure

Default admin fee: **10%**

Example:
- Customer pays: 50,000 TSH
- Admin fee (10%): 5,000 TSH
- Tenant receives: 45,000 TSH

This can be configured in the `initiate_payment` function.

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid checksum | Webhook signature verification failed | Check CLICKPESA_CHECKSUM key |
| Tenant not found | Tenant ID doesn't exist | Register tenant first |
| Mobile number not configured | Tenant has no mobile number | Update tenant with mobile number |
| Invalid network | Network not in [airtel, tigo, halotel] | Select valid network |
| Invalid phone number | Phone has less than 9 digits | Enter valid phone number |

## Production Deployment

### 1. Update Environment Variables
```bash
# Use production ClickPesa credentials
CLICKPESA_API_KEY=production_api_key
CLICKPESA_CHECKSUM=production_checksum
CLICKPESA_WEBHOOK_URL=https://yourdomain.com/api/payments/clickpesa/webhook
```

### 2. Configure Database
```bash
# Use production MySQL instance
DATABASE_URL=mysql+pymysql://prod_user:prod_pass@prod_host/prod_db
```

### 3. Enable HTTPS
```bash
# Ensure all communications are over HTTPS
API_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### 4. Set Up Monitoring
- Monitor webhook failures
- Track transaction status
- Alert on fee collection failures
- Log all payment events

## Frontend Components

### Customer Payment Page
**Location:** `/app/customer/payments/page.tsx`

Features:
- Payment method selection with network logos
- Phone number input with validation
- Payment confirmation dialog
- Processing status animation
- Success/failure screens
- Responsive design

### Admin Dashboard
**Location:** `/app/admin/payments/page.tsx`

Features:
- Tenant registration form
- Tenant list with search
- Transaction history per tenant
- Admin fee logs
- Statistics cards
- Export functionality

## Backend Modules

### clickpesa_client.py
- `ClickPesaClient` class for API interactions
- HMAC SHA256 webhook verification
- Payment initiation
- Payout processing
- Webhook event parsing

### routers/clickpesa_payments.py
- Tenant management endpoints
- Payment initiation endpoint
- Webhook handling endpoint
- Transaction query endpoints
- Admin fee endpoints
- Dashboard endpoint

## Utility Functions

**Location:** `/lib/payment-utils.ts`

Functions:
- `initiatePaymentFlow()` - Start payment session
- `createClickPesaPayment()` - Call payment API
- `getPaymentStatus()` - Check payment status
- `formatPhoneNumber()` - Format phone display
- `isValidPhoneNumber()` - Validate phone
- `detectNetworkFromPhone()` - Auto-detect network
- `calculateAdminFee()` - Calculate fee percentage
- `calculateTenantAmount()` - Calculate tenant share

## Support & Troubleshooting

### Common Issues

1. **Webhook not received**
   - Check ngrok is running
   - Verify CLICKPESA_WEBHOOK_URL is correct
   - Check firewall/port forwarding

2. **Checksum verification fails**
   - Verify CLICKPESA_CHECKSUM value
   - Check webhook signature header
   - Ensure payload is not modified

3. **Tenant transactions not showing**
   - Verify tenant_id is correct
   - Check tenant has clickpesa_enabled=true
   - Verify database connection

4. **Payment processing hangs**
   - Check network connectivity
   - Verify ClickPesa API is accessible
   - Check API credentials

## Future Enhancements

1. **Real ClickPesa Integration**
   - Replace mock responses with actual API calls
   - Handle live webhook events

2. **Reporting & Analytics**
   - Transaction reports
   - Revenue trends
   - Network-wise breakdown

3. **Reconciliation**
   - Automated fee payout
   - Dispute handling
   - Refund processing

4. **Mobile App**
   - Native mobile client
   - Push notifications
   - Offline capabilities

## License

Proprietary - Confidential

## Support

For issues or questions, contact support@yourdomain.com
