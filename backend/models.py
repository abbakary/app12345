from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(String(36), primary_key=True, index=True)  # For UUID
    name = Column(String(255))
    email = Column(String(255), nullable=True)  # Restaurant contact email
    phone = Column(String(20), nullable=True)  # Restaurant contact phone
    address = Column(String(500), nullable=True)
    airpay_account_id = Column(String(100), nullable=True)  # Airpay sub-account ID
    payment_status = Column(String(20), default="pending")  # 'pending', 'active', 'failed'
    customer_portal_url = Column(String(255), nullable=True, unique=True, index=True)  # e.g., 'restaurant-name-unique'
    logo_url = Column(String(500), nullable=True)  # URL to restaurant logo
    # ClickPesa integration fields
    clickpesa_mobile_number = Column(String(20), nullable=True)  # Tenant mobile number to receive payments
    clickpesa_enabled = Column(Boolean, default=False)  # Whether ClickPesa is enabled for this tenant
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"), nullable=True) # Nullable for SysAdmins
    name = Column(String(255), nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    role = Column(String(50))  # 'sysadmin', 'admin', 'reception', 'kitchen', 'customer'
    pin = Column(String(10), nullable=True)  # For PIN codes
    hashed_password = Column(String(255))
    phone = Column(String(20), nullable=True)  # For customers
    created_at = Column(DateTime, default=datetime.utcnow)

class RestaurantTable(Base):
    __tablename__ = "tables"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    name = Column(String(100))
    capacity = Column(Integer)
    status = Column(String(20))
    current_order_id = Column(String(36), nullable=True)
    position_row = Column(Integer)
    position_col = Column(Integer)
    seats = Column(Integer, default=4)

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    name = Column(String(255))
    price = Column(Float)
    category = Column(String(100))
    description = Column(String(500), nullable=True)
    available = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255), nullable=True)
    vehicle_type = Column(String(50))  # 'motorcycle', 'car', 'bicycle', etc.
    vehicle_plate = Column(String(20), nullable=True)
    rating = Column(Float, default=5.0)
    is_available = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)  # Current location
    longitude = Column(Float, nullable=True)  # Current location
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="driver")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # For customer portal orders
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=True)  # Driver assigned to delivery order
    table_id = Column(String(36), nullable=True)  # Nullable for delivery/pickup
    table_name = Column(String(100), nullable=True)  # Nullable for delivery/pickup
    customer_count = Column(Integer, nullable=True)
    order_type = Column(String(20), default="dine-in")  # 'dine-in', 'delivery', 'pickup'
    delivery_address = Column(String(500), nullable=True)  # For delivery orders
    customer_phone = Column(String(20), nullable=True)  # For delivery/pickup orders
    approval_status = Column(String(20), default="pending")  # 'pending', 'approved', 'rejected'
    approval_notes = Column(String(500), nullable=True)  # Reception notes on approval/rejection
    status = Column(String(20))  # 'pending', 'preparing', 'ready', 'paid', 'cancelled'
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    coupon_code = Column(String(50), nullable=True)  # Unique identity for customer pickup/delivery
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    prepared_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    items_modified_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)  # When reception approved the order
    rejected_at = Column(DateTime, nullable=True)  # When reception rejected the order
    assigned_at = Column(DateTime, nullable=True)  # When driver was assigned

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    driver = relationship("Driver", back_populates="orders")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"))
    menu_item_id = Column(String(36), ForeignKey("menu_items.id"))
    quantity = Column(Integer)
    notes = Column(String(500), nullable=True)
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    order_id = Column(String(36))
    amount = Column(Float)
    platform_fee = Column(Float, default=0.0)  # Platform commission (e.g., 10%)
    restaurant_amount = Column(Float, default=0.0)  # Amount for restaurant
    method = Column(String(50))
    status = Column(String(20))  # 'PENDING', 'SUCCESS', 'FAILED'
    transaction_id = Column(String(100), nullable=True)  # Airpay transaction ID
    airpay_transaction_id = Column(String(100), nullable=True)  # Airpay reference
    webhook_processed = Column(String(100), nullable=True)  # Idempotency key
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    title = Column(String(255))
    message = Column(Text)  # Changed to Text for longer messages
    type = Column(String(20))  # 'order', 'payment', 'system'
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RestaurantMessageTemplate(Base):
    __tablename__ = "restaurant_message_templates"
    id = Column(String(36), primary_key=True, index=True)  # FIXED: Added length
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    template_name = Column(String(100))  # e.g., "Portal Sharing", "Welcome", "Promotion"
    message_type = Column(String(20))  # 'sms', 'whatsapp'
    content = Column(Text)  # Changed to Text for longer template content
    is_default = Column(Boolean, default=False)  # Set one as default per restaurant
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"))
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Nullable for 'all' message
    template_id = Column(String(36), ForeignKey("restaurant_message_templates.id"), nullable=True)
    message_type = Column(String(20))  # 'sms', 'whatsapp'
    content = Column(Text)  # Changed to Text for longer messages
    target = Column(String(20))  # 'all', 'new' (customers who haven't received a message yet)
    phone_number = Column(String(20))
    status = Column(String(20), default="pending")  # 'pending', 'sent', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String(500), nullable=True)

class ClickPesaTransaction(Base):
    """
    ClickPesa transaction model for mobile money payments
    Tracks payment requests to ClickPesa, webhooks, and payout status
    """
    __tablename__ = "clickpesa_transactions"
    id = Column(String(36), primary_key=True, index=True)
    tenant_id = Column(String(36), ForeignKey("restaurants.id"))  # Restaurant/Tenant
    reference = Column(String(100), unique=True, index=True)  # Unique transaction reference
    amount = Column(Float)  # Full transaction amount
    admin_fee = Column(Float, default=0.0)  # Platform admin fee
    tenant_amount = Column(Float, default=0.0)  # Amount to be sent to tenant
    network = Column(String(20))  # 'airtel', 'tigo', 'halotel'
    customer_phone = Column(String(20))  # Customer's mobile number
    tenant_mobile = Column(String(20))  # Tenant's mobile number (recipient)
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'received', 'failed'
    payment_status = Column(String(20), default="initiated")  # Payment status from ClickPesa: 'initiated', 'confirmed', 'failed'
    payout_status = Column(String(20), default="pending")  # 'pending', 'initiated', 'completed', 'failed', 'reversed'
    clickpesa_transaction_id = Column(String(100), nullable=True, index=True)  # ClickPesa transaction ID
    webhook_events = Column(JSON, default=list)  # Store webhook events for audit trail
    metadata = Column(JSON, nullable=True)  # Additional data (order_id, customer_name, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    webhook_processed_at = Column(DateTime, nullable=True)

class AdminFeeLog(Base):
    """
    Log of admin fees collected from transactions
    Tracks fees separately for payout management
    """
    __tablename__ = "admin_fee_logs"
    id = Column(String(36), primary_key=True, index=True)
    transaction_id = Column(String(36), ForeignKey("clickpesa_transactions.id"))
    amount = Column(Float)  # Admin fee amount
    fee_percentage = Column(Float, default=10.0)  # Percentage used to calculate fee
    status = Column(String(20), default="collected")  # 'collected', 'pending_payout', 'paid_out'
    payout_id = Column(String(100), nullable=True)  # Reference to payout transaction
    payout_date = Column(DateTime, nullable=True)  # When the fee was paid out
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
