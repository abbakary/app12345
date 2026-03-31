from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import os

class RestaurantBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    admin_email: str
    admin_password: str
    admin_pin: str
    logo_url: Optional[str] = None

class Restaurant(RestaurantBase):
    id: str
    airpay_account_id: Optional[str] = None
    payment_status: str = "pending"
    customer_portal_url: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime

    @validator("logo_url", pre=True, always=True)
    def format_logo_url(cls, v):
        if isinstance(v, str) and v.startswith("/static/"):
            return f"http://localhost:8000{v}"
        return v

    class Config:
        from_attributes = True

class RestaurantPortalConfig(BaseModel):
    """Configuration for restaurant's customer portal"""
    restaurant_id: str
    name: str
    logo_url: Optional[str] = None
    customer_portal_url: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    @validator("logo_url", pre=True, always=True)
    def format_logo_url(cls, v):
        if isinstance(v, str) and v.startswith("/static/"):
            return f"http://localhost:8000{v}"
        return v

    class Config:
        from_attributes = True

class MenuItemBase(BaseModel):
    restaurant_id: str
    name: str
    price: float
    category: str
    description: Optional[str] = None
    available: bool = True
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class MenuItem(MenuItemBase):
    id: str

    @validator("image_url", pre=True, always=True)
    def format_image_url(cls, v):
        if isinstance(v, str) and v.startswith("/static/"):
            return f"http://localhost:8000{v}"
        return v

    class Config:
        from_attributes = True

class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None
    available: bool = True
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class OrderItemBase(BaseModel):
    menu_item_id: str
    quantity: int
    notes: Optional[str] = None

class OrderItem(OrderItemBase):
    id: int
    order_id: str
    menu_item: MenuItem
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    restaurant_id: str
    table_id: Optional[str] = None
    table_name: Optional[str] = None
    customer_count: Optional[int] = None
    status: str
    subtotal: float
    tax: float
    total: float
    coupon_code: Optional[str] = None

class OrderCreate(BaseModel):
    table_id: Optional[str] = None
    table_name: Optional[str] = None
    customer_count: Optional[int] = None
    status: str
    subtotal: float
    tax: float
    total: float
    items: List[OrderItemBase]
    order_type: str = "dine-in"  # 'dine-in', 'delivery', 'pickup'
    delivery_address: Optional[str] = None
    customer_phone: Optional[str] = None

class CustomerOrderCreate(BaseModel):
    order_type: str  # 'dine-in', 'delivery', 'pickup'
    table_id: Optional[str] = None  # Required for dine-in
    delivery_address: Optional[str] = None  # Required for delivery
    customer_phone: Optional[str] = None
    subtotal: float
    tax: float
    total: float
    items: List[OrderItemBase]

class OrderUpdate(BaseModel):
    status: Optional[str] = None

class OrderUpdateItems(BaseModel):
    items: List[OrderItemBase]

class Order(OrderBase):
    id: str
    created_at: datetime
    updated_at: datetime
    prepared_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    items_modified_at: Optional[datetime] = None
    customer_id: Optional[str] = None
    order_type: str = "dine-in"
    delivery_address: Optional[str] = None
    customer_phone: Optional[str] = None
    approval_status: str = "pending"
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    driver_id: Optional[str] = None
    driver: Optional["Driver"] = None
    coupon_code: Optional[str] = None
    items: List[OrderItem]

    class Config:
        from_attributes = True

class OrderApprovalRequest(BaseModel):
    approval_status: str  # 'approved' or 'rejected'
    approval_notes: Optional[str] = None

class TablePosition(BaseModel):
    row: int
    col: int

class TableBase(BaseModel):
    restaurant_id: str
    name: str
    capacity: int
    status: str
    current_order_id: Optional[str] = None
    position: TablePosition
    seats: int = 4

class TableCreate(BaseModel):
    name: str
    capacity: int
    status: str = "available"
    position: TablePosition
    seats: int = 4

class RestaurantTable(BaseModel):
    id: str
    restaurant_id: str
    name: str
    capacity: int
    status: str
    current_order_id: Optional[str] = None
    position: TablePosition
    seats: int = 4

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    order_id: str
    amount: float
    method: str = "airpay"
    status: str = "PENDING"
    transaction_id: Optional[str] = None

class Payment(PaymentBase):
    id: str
    restaurant_id: str
    platform_fee: float = 0.0
    restaurant_amount: float = 0.0
    airpay_transaction_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class PaymentInitiateRequest(BaseModel):
    order_id: str
    amount: float
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    platform_fee_percentage: float = 10.0

class NotificationBase(BaseModel):
    type: str
    message: str
    order_id: Optional[str] = None
    table_id: Optional[str] = None

class Notification(NotificationBase):
    id: str
    read: bool
    created_at: datetime
    class Config:
        from_attributes = True

class AppStats(BaseModel):
    todaySales: float
    todayOrders: int
    completedToday: int
    pendingOrders: int
    preparingOrders: int
    pendingApprovalOrders: int

class LoginRequest(BaseModel):
    email: str
    password: str

class PinLoginRequest(BaseModel):
    pin: str

class AuthToken(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    restaurant_id: Optional[str] = None

class UserBase(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: str
    restaurant_id: Optional[str] = None
    pin: Optional[str] = None
    phone: Optional[str] = None


class User(UserBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class PlatformStats(BaseModel):
    total_tenants: int
    total_users: int
    total_orders: int
    total_revenue: float

class CustomerRegisterRequest(BaseModel):
    username: str
    phone: str
    password: str

class CustomerLoginRequest(BaseModel):
    username: str
    password: str

class CustomerAuthToken(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    restaurant_id: str
    name: Optional[str] = None
    username: str

class DriverBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    vehicle_type: str
    vehicle_plate: Optional[str] = None
    rating: float = 5.0
    is_available: bool = True

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    rating: Optional[float] = None
    is_available: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Driver(DriverBase):
    id: str
    restaurant_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverAssignRequest(BaseModel):
    driver_id: str

class CustomerLocationUpdate(BaseModel):
    order_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: datetime = None

    @validator("timestamp", pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()

class MessageBase(BaseModel):
    message_type: str  # 'sms', 'whatsapp'
    content: str
    target: str  # 'all', 'new'

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    restaurant_id: str
    customer_id: Optional[str] = None
    phone_number: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class MessageTemplateBase(BaseModel):
    template_name: str
    message_type: str  # 'sms', 'whatsapp'
    content: str
    is_default: bool = False

class MessageTemplateCreate(MessageTemplateBase):
    pass

class MessageTemplate(MessageTemplateBase):
    id: str
    restaurant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    success: bool
    message: str
    messages_sent: int = 0
    messages_failed: int = 0

# ClickPesa Payment Schemas
class TenantCreateRequest(BaseModel):
    """Request to register a new tenant (restaurant)"""
    name: str
    mobile_number: str  # Mobile number to receive payments
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    metadata: Optional[dict] = None

class TenantUpdate(BaseModel):
    """Update tenant information"""
    name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    clickpesa_enabled: Optional[bool] = None

class TenantResponse(BaseModel):
    """Response with tenant information"""
    id: str
    name: str
    mobile_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    clickpesa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ClickPesaPaymentInitiate(BaseModel):
    """Request to initiate a ClickPesa payment"""
    amount: float
    network: str  # 'airtel', 'tigo', 'halotel'
    customer_phone: str  # Customer's mobile number
    tenant_id: str  # Which tenant to pay
    order_reference: Optional[str] = None
    metadata: Optional[dict] = None

class ClickPesaTransactionResponse(BaseModel):
    """Response from payment initiation"""
    id: str
    reference: str
    amount: float
    admin_fee: float
    tenant_amount: float
    network: str
    customer_phone: str
    status: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ClickPesaWebhookPayload(BaseModel):
    """ClickPesa webhook payload"""
    event: str  # 'payment_received', 'payment_failed', 'payout_initiated', etc.
    transaction_id: str
    reference: str
    amount: Optional[float] = None
    network: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None
    checksum: Optional[str] = None

class AdminFeeLogResponse(BaseModel):
    """Response for admin fee log"""
    id: str
    transaction_id: str
    amount: float
    fee_percentage: float
    status: str
    payout_id: Optional[str] = None
    payout_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TenantTransactionHistory(BaseModel):
    """Transaction history for a specific tenant"""
    total_revenue: float
    total_admin_fees: float
    transactions_count: int
    pending_count: int
    successful_count: int
    failed_count: int

class PaymentStatusResponse(BaseModel):
    """Response for payment status"""
    id: str
    reference: str
    amount: float
    status: str
    payment_status: str
    payout_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
