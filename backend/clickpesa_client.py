"""
ClickPesa API client for mobile money payment integration
Handles payment initiation, webhook verification, and transaction tracking
"""
import httpx
import hmac
import hashlib
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClickPesaClient:
    """ClickPesa mobile money payment client"""

    def __init__(
        self,
        api_key: str = None,
        checksum_key: str = None,
        base_url: str = None,
        webhook_url: str = None,
    ):
        """
        Initialize ClickPesa client

        Args:
            api_key: ClickPesa API key
            checksum_key: HMAC SHA256 checksum key for webhook verification
            base_url: ClickPesa API base URL
            webhook_url: Your webhook URL for ClickPesa to send events
        """
        self.api_key = api_key or os.getenv("CLICKPESA_API_KEY")
        self.checksum_key = checksum_key or os.getenv("CLICKPESA_CHECKSUM")
        self.base_url = base_url or os.getenv("CLICKPESA_BASE_URL", "https://api.clickpesa.com")
        self.webhook_url = webhook_url or os.getenv("CLICKPESA_WEBHOOK_URL")

        if not self.api_key:
            logger.warning("CLICKPESA_API_KEY not set")
        if not self.checksum_key:
            logger.warning("CLICKPESA_CHECKSUM not set")

        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def initiate_payment(
        self,
        amount: float,
        customer_phone: str,
        recipient_number: str,
        network: str,
        reference: str,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a payment request with ClickPesa

        Args:
            amount: Transaction amount
            customer_phone: Customer's mobile number
            recipient_number: Tenant's mobile number (to receive payment)
            network: Mobile network ('airtel', 'tigo', 'halotel')
            reference: Unique transaction reference
            callback_url: Webhook URL for callbacks

        Returns:
            Dict with transaction details or error
        """
        try:
            callback_url = callback_url or self.webhook_url

            # Prepare payment request
            payload = {
                "amount": amount,
                "customer_phone": customer_phone,
                "recipient_number": recipient_number,
                "network": network,
                "reference": reference,
                "callback_url": callback_url,
                "timestamp": datetime.utcnow().isoformat(),
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            logger.info(f"Initiating ClickPesa payment: {reference}")

            # In production, call actual ClickPesa API
            # For now, return mock response for testing
            response = await self._mock_payment_request(payload)

            logger.info(f"ClickPesa response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _mock_payment_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock payment request for testing
        In production, this would call the real ClickPesa API
        """
        # For testing, we'll return a successful mock response
        return {
            "success": True,
            "transaction_id": f"clickpesa_{payload['reference']}",
            "reference": payload["reference"],
            "status": "initiated",
            "amount": payload["amount"],
            "network": payload["network"],
        }

    def verify_webhook_checksum(self, payload: str, provided_checksum: str) -> bool:
        """
        Verify webhook signature using HMAC SHA256

        Args:
            payload: The webhook payload as JSON string
            provided_checksum: The checksum from webhook header

        Returns:
            True if checksum is valid, False otherwise
        """
        if not self.checksum_key:
            logger.error("Checksum key not configured")
            return False

        try:
            # Create HMAC SHA256 hash
            calculated_checksum = hmac.new(
                self.checksum_key.encode(),
                payload.encode() if isinstance(payload, str) else payload,
                hashlib.sha256,
            ).hexdigest()

            # Constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(calculated_checksum, provided_checksum)

            if not is_valid:
                logger.warning(
                    f"Invalid checksum. Expected: {calculated_checksum}, "
                    f"Received: {provided_checksum}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying checksum: {str(e)}")
            return False

    def parse_webhook_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate webhook event from ClickPesa

        Args:
            data: Webhook payload

        Returns:
            Parsed event data
        """
        return {
            "event": data.get("event"),
            "transaction_id": data.get("transaction_id"),
            "reference": data.get("reference"),
            "amount": data.get("amount"),
            "network": data.get("network"),
            "status": data.get("status"),
            "timestamp": data.get("timestamp"),
            "recipient_number": data.get("recipient_number"),
            "customer_number": data.get("customer_number"),
        }

    async def process_payout(
        self,
        recipient_number: str,
        amount: float,
        reference: str,
    ) -> Dict[str, Any]:
        """
        Process payout to admin account

        Args:
            recipient_number: Recipient mobile number
            amount: Payout amount
            reference: Unique reference for payout

        Returns:
            Payout response
        """
        try:
            payload = {
                "recipient_number": recipient_number,
                "amount": amount,
                "reference": reference,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Processing payout: {reference}")

            # In production, call actual ClickPesa payout API
            return {
                "success": True,
                "payout_id": f"payout_{reference}",
                "reference": reference,
                "amount": amount,
                "status": "initiated",
            }

        except Exception as e:
            logger.error(f"Error processing payout: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


# Global instance
clickpesa_client = ClickPesaClient()
