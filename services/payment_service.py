"""
Payment service for AI Market Insight Bot.
Handles cryptocurrency payment processing via NOWPayments API.
"""

import logging
import aiohttp
import hmac
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from core.metrics import MetricsCollector
import config

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for payment operations.
    
    Provides:
    - NOWPayments API integration
    - Invoice generation
    - Payment tracking
    - Webhook signature verification
    - Payment confirmation processing
    """
    
    def __init__(
        self,
        payment_repo: PaymentRepository,
        subscription_repo: SubscriptionRepository,
        metrics: MetricsCollector
    ):
        """
        Initialize payment service.
        
        Args:
            payment_repo: Payment repository
            subscription_repo: Subscription repository
            metrics: Metrics collector
        """
        self.payment_repo = payment_repo
        self.subscription_repo = subscription_repo
        self.metrics = metrics
        
        # NOWPayments configuration
        self.api_key = config.NOWPAYMENTS_API_KEY
        self.ipn_secret = config.NOWPAYMENTS_IPN_SECRET
        self.api_url = config.NOWPAYMENTS_API_URL
        self.supported_currencies = config.SUPPORTED_CURRENCIES
        
        logger.info("PaymentService initialized")
    
    async def create_invoice(
        self,
        subscription_id: int,
        group_id: int,
        amount_usd: float,
        currency: str = "btc",
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a payment invoice via NOWPayments.
        
        Args:
            subscription_id: Subscription ID
            group_id: Telegram group ID
            amount_usd: Amount in USD
            currency: Cryptocurrency (btc, eth, usdt, etc.)
            description: Invoice description
            
        Returns:
            Invoice data or None
        """
        try:
            if not self.api_key:
                logger.error("NOWPayments API key not configured")
                return None
            
            # Validate currency
            if currency.lower() not in self.supported_currencies:
                logger.error(f"Unsupported currency: {currency}")
                return None
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(
                minutes=config.PAYMENT_INVOICE_EXPIRATION_MINUTES
            )
            
            # Prepare invoice data
            invoice_data = {
                "price_amount": amount_usd,
                "price_currency": "usd",
                "pay_currency": currency.lower(),
                "order_id": f"sub_{subscription_id}_{int(datetime.now().timestamp())}",
                "order_description": description or f"Subscription for group {group_id}",
                "ipn_callback_url": config.WEBHOOK_URL if config.WEBHOOK_URL else None,
                "success_url": None,  # Can be set to a success page
                "cancel_url": None    # Can be set to a cancel page
            }
            
            # Create invoice via NOWPayments API
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/invoice",
                    headers=headers,
                    json=invoice_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"NOWPayments API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
            
            # Create payment record in database
            payment = await self.payment_repo.create({
                'subscription_id': subscription_id,
                'group_id': group_id,
                'amount_usd': amount_usd,
                'currency': currency.lower(),
                'payment_status': 'pending',
                'payment_url': result.get('invoice_url'),
                'invoice_id': result.get('id'),
                'payment_id_external': result.get('payment_id'),
                'payment_address': result.get('pay_address'),
                'amount_crypto': result.get('pay_amount'),
                'expires_at': expires_at.isoformat(),
                'webhook_data': json.dumps(result)
            })
            
            if not payment:
                logger.error("Failed to create payment record")
                return None
            
            # Log event
            await self.subscription_repo.log_event(
                subscription_id,
                group_id,
                'invoice_created',
                {
                    'payment_id': payment['payment_id'],
                    'invoice_id': result.get('id'),
                    'amount_usd': amount_usd,
                    'currency': currency
                }
            )
            
            self.metrics.inc_counter("invoices_created")
            logger.info(f"Created invoice for subscription {subscription_id}: {result.get('id')}")
            
            return {
                'payment_id': payment['payment_id'],
                'invoice_id': result.get('id'),
                'payment_url': result.get('invoice_url'),
                'pay_address': result.get('pay_address'),
                'pay_amount': result.get('pay_amount'),
                'pay_currency': currency.lower(),
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return None
    
    async def get_payment_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get payment status from NOWPayments.
        
        Args:
            invoice_id: NOWPayments invoice ID
            
        Returns:
            Payment status data or None
        """
        try:
            if not self.api_key:
                logger.error("NOWPayments API key not configured")
                return None
            
            headers = {
                "x-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/invoice/{invoice_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"NOWPayments API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting payment status: {e}", exc_info=True)
            return None
    
    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str
    ) -> bool:
        """
        Verify NOWPayments webhook signature.

        Args:
            payload: Webhook payload (raw JSON string)
            signature: HMAC signature from header

        Returns:
            True if signature is valid
        """
        try:
            if not self.ipn_secret:
                # SECURITY: Only allow bypass in development
                if config.IS_PRODUCTION:
                    logger.error("IPN secret not configured in PRODUCTION - rejecting webhook")
                    self.metrics.inc_counter("webhook_signature_missing_secret")
                    return False
                else:
                    logger.warning("IPN secret not configured, skipping signature verification (DEVELOPMENT ONLY)")
                    return True

            # Calculate expected signature
            expected_signature = hmac.new(
                self.ipn_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()

            # Compare signatures (timing-safe comparison)
            is_valid = hmac.compare_digest(signature, expected_signature)

            if not is_valid:
                logger.warning("Invalid webhook signature")
                self.metrics.inc_counter("webhook_signature_invalid")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}", exc_info=True)
            return False
    
    async def process_payment_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process payment webhook from NOWPayments.
        
        Args:
            webhook_data: Webhook payload data
            
        Returns:
            True if processed successfully
        """
        try:
            invoice_id = webhook_data.get('invoice_id')
            payment_status = webhook_data.get('payment_status')
            
            if not invoice_id:
                logger.error("Webhook missing invoice_id")
                return False
            
            # Find payment record
            payment = await self.payment_repo.find_by_invoice_id(str(invoice_id))
            
            if not payment:
                logger.error(f"Payment not found for invoice: {invoice_id}")
                return False
            
            # Update payment record
            update_data = {
                'payment_status': payment_status,
                'transaction_hash': webhook_data.get('payment_hash'),
                'confirmations': webhook_data.get('confirmations', 0),
                'webhook_data': json.dumps(webhook_data)
            }
            
            # If payment is confirmed, set confirmed_at
            if payment_status in ['finished', 'confirmed']:
                update_data['confirmed_at'] = datetime.now().isoformat()
            
            await self.payment_repo.update(payment['payment_id'], update_data)
            
            # Log event
            await self.subscription_repo.log_event(
                payment['subscription_id'],
                payment['group_id'],
                f'payment_{payment_status}',
                webhook_data
            )
            
            # If payment is confirmed, activate subscription
            if payment_status == 'finished':
                from services.subscription_service import SubscriptionService
                # Note: This will be injected properly in bot.py
                logger.info(f"Payment confirmed for subscription {payment['subscription_id']}")
                self.metrics.inc_counter("payments_confirmed")
            
            logger.info(f"Processed webhook for invoice {invoice_id}: {payment_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing payment webhook: {e}", exc_info=True)
            return False
    
    async def get_available_currencies(self) -> List[str]:
        """
        Get list of available cryptocurrencies from NOWPayments.
        
        Returns:
            List of currency codes
        """
        try:
            if not self.api_key:
                return self.supported_currencies
            
            headers = {
                "x-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/currencies",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.warning("Failed to fetch currencies from NOWPayments")
                        return self.supported_currencies
                    
                    result = await response.json()
                    currencies = result.get('currencies', [])
                    
                    # Filter to only supported currencies
                    return [c for c in currencies if c.lower() in self.supported_currencies]
            
        except Exception as e:
            logger.error(f"Error getting available currencies: {e}", exc_info=True)
            return self.supported_currencies

