"""
ClickPesa payment endpoints for mobile money payments
Handles payment initiation, webhook callbacks, and transaction management
"""
import uuid
import json
import hmac
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks, Request
from sqlalchemy.orm import Session
import logging

from database import get_db
from clickpesa_client import clickpesa_client
import models
import schemas
from auth_utils import verify_restaurant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments/clickpesa", tags=["ClickPesa Payments"])


# ============================================================================
# TENANT MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("/tenants", response_model=schemas.TenantResponse)
def register_tenant(
    request: schemas.TenantCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new tenant (restaurant) for ClickPesa payments
    Admin only endpoint
    """
    # Check if tenant already exists with this mobile number
    existing = db.query(models.Restaurant).filter(
        models.Restaurant.clickpesa_mobile_number == request.mobile_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A tenant with this mobile number already exists",
        )

    # Create new tenant/restaurant
    tenant_id = str(uuid.uuid4())
    tenant = models.Restaurant(
        id=tenant_id,
        name=request.name,
        email=request.email or "",
        phone=request.phone or "",
        address=request.address or "",
        clickpesa_mobile_number=request.mobile_number,
        clickpesa_enabled=True,
        customer_portal_url=None,
        logo_url=None,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    logger.info(f"Tenant registered: {tenant_id} - {request.name}")

    return schemas.TenantResponse.from_orm(tenant)


@router.get("/tenants", response_model=List[schemas.TenantResponse])
def list_tenants(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all registered tenants
    Admin only endpoint
    """
    tenants = db.query(models.Restaurant).filter(
        models.Restaurant.clickpesa_enabled == True
    ).offset(skip).limit(limit).all()

    return [schemas.TenantResponse.from_orm(t) for t in tenants]


@router.get("/tenants/{tenant_id}", response_model=schemas.TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get tenant details by ID
    """
    tenant = db.query(models.Restaurant).filter(
        models.Restaurant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return schemas.TenantResponse.from_orm(tenant)


@router.put("/tenants/{tenant_id}", response_model=schemas.TenantResponse)
def update_tenant(
    tenant_id: str,
    update_data: schemas.TenantUpdate,
    db: Session = Depends(get_db),
):
    """
    Update tenant information
    """
    tenant = db.query(models.Restaurant).filter(
        models.Restaurant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Update fields
    if update_data.name:
        tenant.name = update_data.name
    if update_data.mobile_number:
        tenant.clickpesa_mobile_number = update_data.mobile_number
    if update_data.email:
        tenant.email = update_data.email
    if update_data.address:
        tenant.address = update_data.address
    if update_data.phone:
        tenant.phone = update_data.phone
    if update_data.clickpesa_enabled is not None:
        tenant.clickpesa_enabled = update_data.clickpesa_enabled

    db.commit()
    db.refresh(tenant)

    logger.info(f"Tenant updated: {tenant_id}")

    return schemas.TenantResponse.from_orm(tenant)


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================


@router.post("/initiate", response_model=schemas.ClickPesaTransactionResponse)
async def initiate_payment(
    request: schemas.ClickPesaPaymentInitiate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Initiate a ClickPesa payment request

    Request body:
    - amount: Transaction amount
    - network: Mobile network (airtel, tigo, halotel)
    - customer_phone: Customer's mobile number
    - tenant_id: Tenant (restaurant) ID
    - order_reference: Optional order reference
    - metadata: Optional additional data
    """
    # Validate tenant exists and is enabled
    tenant = db.query(models.Restaurant).filter(
        models.Restaurant.id == request.tenant_id,
        models.Restaurant.clickpesa_enabled == True,
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found or ClickPesa not enabled",
        )

    if not tenant.clickpesa_mobile_number:
        raise HTTPException(
            status_code=400,
            detail="Tenant mobile number not configured",
        )

    # Validate input
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if request.network.lower() not in ["airtel", "tigo", "halotel"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid network. Must be: airtel, tigo, or halotel",
        )

    # Create transaction reference
    reference = f"clickpesa_{uuid.uuid4().hex[:16]}"

    # Calculate admin fee (10% default)
    admin_fee_percentage = 10.0
    admin_fee = request.amount * (admin_fee_percentage / 100)
    tenant_amount = request.amount - admin_fee

    # Create transaction record
    transaction = models.ClickPesaTransaction(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        reference=reference,
        amount=request.amount,
        admin_fee=admin_fee,
        tenant_amount=tenant_amount,
        network=request.network.lower(),
        customer_phone=request.customer_phone,
        tenant_mobile=tenant.clickpesa_mobile_number,
        status="pending",
        payment_status="initiated",
        payout_status="pending",
        metadata=request.metadata or {},
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Initiate payment with ClickPesa
    clickpesa_response = await clickpesa_client.initiate_payment(
        amount=request.amount,
        customer_phone=request.customer_phone,
        recipient_number=tenant.clickpesa_mobile_number,
        network=request.network.lower(),
        reference=reference,
    )

    if not clickpesa_response.get("success"):
        transaction.status = "failed"
        transaction.payment_status = "failed"
        db.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Failed to initiate payment: {clickpesa_response.get('error')}",
        )

    # Update transaction with ClickPesa transaction ID
    transaction.clickpesa_transaction_id = clickpesa_response.get("transaction_id")
    transaction.status = "processing"
    db.commit()
    db.refresh(transaction)

    logger.info(
        f"Payment initiated: {reference} - Amount: {request.amount} - "
        f"Tenant: {request.tenant_id}"
    )

    return schemas.ClickPesaTransactionResponse.from_orm(transaction)


# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================


@router.post("/webhook")
async def handle_clickpesa_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle ClickPesa webhook callbacks

    ClickPesa sends events for:
    - payment_received: Payment successful
    - payment_failed: Payment failed
    - payout_initiated: Payout to tenant started
    - payout_completed: Payout completed
    - payout_failed: Payout failed
    - payout_reversed: Payout reversed

    Webhook authentication:
    - Checksum provided in header or body
    - Verified using HMAC SHA256
    """
    try:
        # Get raw body for checksum verification
        body = await request.body()
        payload = json.loads(body)

        # Get checksum from header or body
        checksum = request.headers.get("X-Checksum") or payload.get("checksum")

        if not checksum:
            logger.error("Webhook received without checksum")
            raise HTTPException(status_code=400, detail="Missing checksum")

        # Verify webhook signature
        if not clickpesa_client.verify_webhook_checksum(body.decode(), checksum):
            logger.error(f"Invalid webhook checksum for payload: {payload}")
            raise HTTPException(status_code=401, detail="Invalid checksum")

        # Parse webhook event
        event_data = clickpesa_client.parse_webhook_event(payload)

        # Find transaction by reference
        transaction = db.query(models.ClickPesaTransaction).filter(
            models.ClickPesaTransaction.reference == event_data["reference"]
        ).first()

        if not transaction:
            logger.warning(f"Webhook received for unknown transaction: {event_data['reference']}")
            return {"status": "ok"}

        # Prevent duplicate processing
        if transaction.webhook_processed_at:
            logger.info(f"Webhook already processed for {event_data['reference']}")
            return {"status": "already_processed"}

        # Process based on event type
        event_type = event_data.get("event")

        if event_type == "payment_received":
            transaction.status = "received"
            transaction.payment_status = "confirmed"
            transaction.payout_status = "initiated"

            # Create admin fee log
            fee_log = models.AdminFeeLog(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                amount=transaction.admin_fee,
                fee_percentage=10.0,
                status="collected",
            )
            db.add(fee_log)

            logger.info(f"Payment received: {event_data['reference']}")

        elif event_type == "payment_failed":
            transaction.status = "failed"
            transaction.payment_status = "failed"
            transaction.payout_status = "failed"
            logger.warning(f"Payment failed: {event_data['reference']}")

        elif event_type == "payout_initiated":
            transaction.payout_status = "initiated"
            logger.info(f"Payout initiated: {event_data['reference']}")

        elif event_type == "payout_completed":
            transaction.payout_status = "completed"
            logger.info(f"Payout completed: {event_data['reference']}")

        elif event_type == "payout_failed":
            transaction.payout_status = "failed"
            logger.warning(f"Payout failed: {event_data['reference']}")

        elif event_type == "payout_reversed":
            transaction.payout_status = "reversed"
            logger.warning(f"Payout reversed: {event_data['reference']}")

        # Update webhook log
        if not transaction.webhook_events:
            transaction.webhook_events = []
        transaction.webhook_events.append({
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data,
        })

        transaction.webhook_processed_at = datetime.utcnow()
        db.commit()

        return {"status": "processed"}

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TRANSACTION QUERY ENDPOINTS
# ============================================================================


@router.get("/transactions/{tenant_id}", response_model=List[schemas.ClickPesaTransactionResponse])
def get_tenant_transactions(
    tenant_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
):
    """
    Get all transactions for a specific tenant
    """
    query = db.query(models.ClickPesaTransaction).filter(
        models.ClickPesaTransaction.tenant_id == tenant_id
    )

    if status:
        query = query.filter(models.ClickPesaTransaction.status == status)

    transactions = query.order_by(
        models.ClickPesaTransaction.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [schemas.ClickPesaTransactionResponse.from_orm(t) for t in transactions]


@router.get("/transactions/status/{reference}", response_model=schemas.PaymentStatusResponse)
def get_transaction_status(
    reference: str,
    db: Session = Depends(get_db),
):
    """
    Get transaction status by reference
    """
    transaction = db.query(models.ClickPesaTransaction).filter(
        models.ClickPesaTransaction.reference == reference
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return schemas.PaymentStatusResponse.from_orm(transaction)


@router.get("/admin-fees/{tenant_id}", response_model=List[schemas.AdminFeeLogResponse])
def get_tenant_admin_fees(
    tenant_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get admin fee logs for a tenant
    """
    # First get all transactions for this tenant
    transactions = db.query(models.ClickPesaTransaction).filter(
        models.ClickPesaTransaction.tenant_id == tenant_id
    ).all()

    transaction_ids = [t.id for t in transactions]

    # Then get fee logs for these transactions
    fee_logs = db.query(models.AdminFeeLog).filter(
        models.AdminFeeLog.transaction_id.in_(transaction_ids)
    ).order_by(models.AdminFeeLog.created_at.desc()).offset(skip).limit(limit).all()

    return [schemas.AdminFeeLogResponse.from_orm(fl) for fl in fee_logs]


@router.get("/dashboard/{tenant_id}", response_model=schemas.TenantTransactionHistory)
def get_tenant_dashboard(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get dashboard stats for a tenant
    """
    transactions = db.query(models.ClickPesaTransaction).filter(
        models.ClickPesaTransaction.tenant_id == tenant_id
    ).all()

    total_revenue = sum(t.tenant_amount for t in transactions)
    total_admin_fees = sum(t.admin_fee for t in transactions)
    pending_count = len([t for t in transactions if t.status == "pending"])
    successful_count = len([t for t in transactions if t.status == "received"])
    failed_count = len([t for t in transactions if t.status == "failed"])

    return schemas.TenantTransactionHistory(
        total_revenue=total_revenue,
        total_admin_fees=total_admin_fees,
        transactions_count=len(transactions),
        pending_count=pending_count,
        successful_count=successful_count,
        failed_count=failed_count,
    )
