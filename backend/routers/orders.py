from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import random
import string
from datetime import datetime

def generate_coupon_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

from database import get_db
from websocket_manager import manager
import models, schemas

from auth_utils import verify_restaurant

def create_notification(db: Session, restaurant_id: str, title: str, message: str, notification_type: str):
    """Helper function to create a notification"""
    notification = models.Notification(
        id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        title=title,
        message=message,
        type=notification_type,
        read=False
    )
    db.add(notification)
    db.commit()
    return notification

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("", response_model=List[schemas.Order])
def get_orders(db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    return db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.restaurant_id == restaurant_id)\
        .order_by(models.Order.created_at.desc())\
        .all()

@router.get("/active", response_model=List[schemas.Order])
def get_active_orders(db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    return db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.restaurant_id == restaurant_id)\
        .filter(models.Order.approval_status == "approved")\
        .filter(models.Order.status != "paid")\
        .filter(models.Order.status != "cancelled")\
        .all()

@router.get("/pending-approval", response_model=List[schemas.Order])
def get_pending_approval_orders(db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    """Get all customer orders pending reception approval"""
    return db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.restaurant_id == restaurant_id)\
        .filter(models.Order.approval_status == "pending")\
        .order_by(models.Order.created_at.desc())\
        .all()

@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: str, db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    order = db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.restaurant_id == restaurant_id)\
        .filter(models.Order.id == order_id)\
        .first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("", response_model=schemas.Order)
async def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(verify_restaurant),
    x_customer_id: Optional[str] = Header(None)
):
    print(f"Creating order for restaurant {restaurant_id}, customer {x_customer_id}")
    # If x_customer_id is an empty string, treat it as None
    customer_id = x_customer_id if x_customer_id and x_customer_id.strip() else None
    
    # Portal orders are customer-initiated orders without table assignment (pickup/delivery)
    # Reception orders are staff-initiated or have table assignment (dine-in)
    is_portal_order = customer_id is not None and not order_data.table_id
    print(f"Is portal order: {is_portal_order} (customer_id: {customer_id}, table_id: {order_data.table_id})")
    
    try:
        db_order = models.Order(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            customer_id=customer_id,
            table_id=order_data.table_id,
            table_name=order_data.table_name,
            customer_count=order_data.customer_count,
            status=order_data.status,
            subtotal=order_data.subtotal,
            tax=order_data.tax,
            total=order_data.total,
            order_type=order_data.order_type,
            delivery_address=order_data.delivery_address,
            customer_phone=order_data.customer_phone,
            coupon_code=generate_coupon_code() if is_portal_order else None,
            approval_status="pending" if is_portal_order else "approved"
        )
        db.add(db_order)

        for item in order_data.items:
            # Verify menu item exists to avoid ResponseValidationError later
            menu_item = db.query(models.MenuItem).filter(models.MenuItem.id == item.menu_item_id).first()
            if not menu_item:
                print(f"Error: Menu item {item.menu_item_id} not found")
                raise HTTPException(status_code=400, detail=f"Menu item {item.menu_item_id} not found")
                
            db_item = models.OrderItem(
                order_id=db_order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                notes=item.notes
            )
            db.add(db_item)

        # Only update table if it's a dine-in table order
        if order_data.table_id and not is_portal_order:
            table = db.query(models.RestaurantTable).filter(
                models.RestaurantTable.restaurant_id == restaurant_id,
                models.RestaurantTable.id == order_data.table_id
            ).first()
            if table:
                table.status = "occupied"
                table.current_order_id = db_order.id

        db.commit()
        print(f"Order {db_order.id} committed successfully with coupon {db_order.coupon_code}")

        # Create notification for new order
        if is_portal_order:
            create_notification(
                db,
                restaurant_id,
                title="New Customer Order",
                message=f"New order from customer: {order_data.customer_phone or 'Unknown'} for {order_data.total}",
                notification_type="new_order"
            )
        else:
            create_notification(
                db,
                restaurant_id,
                title="New Order",
                message=f"New order placed for table {order_data.table_name} - Total: {order_data.total}",
                notification_type="new_order"
            )
    except Exception as e:
        db.rollback()
        print(f"Error creating order: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Refresh with eager loading to avoid ResponseValidationError
    refreshed_order = db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.id == db_order.id)\
        .first()

    event_type = "NEW_CUSTOMER_ORDER" if is_portal_order else "NEW_ORDER"
    await manager.broadcast_update({"type": event_type, "order_id": db_order.id})
    return refreshed_order

@router.patch("/{order_id}", response_model=schemas.Order)
async def update_order_status(order_id: str, updates: schemas.OrderUpdate, db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    db_order = db.query(models.Order).filter(models.Order.restaurant_id == restaurant_id).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = db_order.status
    if updates.status:
        db_order.status = updates.status
        if updates.status == "preparing":
            db_order.prepared_at = datetime.utcnow()

    db.commit()

    # Create notification based on status change
    if updates.status and updates.status != old_status:
        if updates.status == "preparing":
            create_notification(
                db,
                restaurant_id,
                title="Order Started",
                message=f"Order {order_id[:8]} is now being prepared",
                notification_type="order_started"
            )
        elif updates.status == "ready":
            create_notification(
                db,
                restaurant_id,
                title="Order Ready",
                message=f"Order {order_id[:8]} is ready for pickup/serving",
                notification_type="order_ready"
            )
        elif updates.status == "served":
            create_notification(
                db,
                restaurant_id,
                title="Order Served",
                message=f"Order {order_id[:8]} has been served",
                notification_type="order_served"
            )
        elif updates.status == "paid":
            create_notification(
                db,
                restaurant_id,
                title="Order Paid",
                message=f"Order {order_id[:8]} payment has been received",
                notification_type="order_paid"
            )
        elif updates.status == "cancelled":
            create_notification(
                db,
                restaurant_id,
                title="Order Cancelled",
                message=f"Order {order_id[:8]} has been cancelled",
                notification_type="order_cancelled"
            )

    # Refresh with eager loading
    refreshed_order = db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.id == order_id)\
        .first()

    await manager.broadcast_update({"type": "ORDER_STATUS_CHANGED", "order_id": db_order.id, "status": db_order.status})
    return refreshed_order

@router.patch("/{order_id}/items", response_model=schemas.Order)
async def update_order_items(order_id: str, updates: schemas.OrderUpdateItems, db: Session = Depends(get_db), restaurant_id: str = Depends(verify_restaurant)):
    db_order = db.query(models.Order).filter(models.Order.restaurant_id == restaurant_id).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()

    for item in updates.items:
        db_item = models.OrderItem(
            order_id=order_id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
            notes=item.notes
        )
        db.add(db_item)

    db_order.items_modified_at = datetime.utcnow()
    db_order.updated_at = datetime.utcnow()

    subtotal = sum([db.query(models.MenuItem).get(i.menu_item_id).price * i.quantity for i in updates.items])
    db_order.subtotal = subtotal
    db_order.tax = subtotal * 0.1
    db_order.total = subtotal * 1.1

    db.commit()

    # Create notification for order items modification
    create_notification(
        db,
        restaurant_id,
        title="Order Items Modified",
        message=f"Order {order_id[:8]} items have been updated",
        notification_type="order_modified"
    )

    # Refresh with eager loading
    refreshed_order = db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.id == order_id)\
        .first()

    await manager.broadcast_update({"type": "ORDER_ITEMS_UPDATED", "order_id": db_order.id})
    return refreshed_order


@router.patch("/{order_id}/approval", response_model=schemas.Order)
async def approve_reject_order(
    order_id: str,
    approval: schemas.OrderApprovalRequest,
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(verify_restaurant)
):
    """Reception approves or rejects a customer order"""
    db_order = db.query(models.Order)\
        .filter(models.Order.restaurant_id == restaurant_id)\
        .filter(models.Order.id == order_id)\
        .first()

    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.approval_status != "pending":
        raise HTTPException(status_code=400, detail="Order is not pending approval")

    db_order.approval_status = approval.approval_status
    db_order.approval_notes = approval.approval_notes

    if approval.approval_status == "approved":
        db_order.approved_at = datetime.utcnow()
        db_order.status = "pending"  # Ready for kitchen
        create_notification(
            db,
            restaurant_id,
            title="Order Approved",
            message=f"Order {order_id[:8]} has been approved and sent to kitchen",
            notification_type="order_approved"
        )
    elif approval.approval_status == "rejected":
        db_order.rejected_at = datetime.utcnow()
        db_order.status = "cancelled"
        create_notification(
            db,
            restaurant_id,
            title="Order Rejected",
            message=f"Order {order_id[:8]} has been rejected. Reason: {approval.approval_notes or 'No reason provided'}",
            notification_type="order_rejected"
        )

    db_order.updated_at = datetime.utcnow()
    db.commit()

    # Refresh with eager loading
    refreshed_order = db.query(models.Order)\
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.menu_item),
                 joinedload(models.Order.driver))\
        .filter(models.Order.id == order_id)\
        .first()

    event_type = "ORDER_APPROVED" if approval.approval_status == "approved" else "ORDER_REJECTED"
    await manager.broadcast_update({"type": event_type, "order_id": db_order.id})
    return refreshed_order
