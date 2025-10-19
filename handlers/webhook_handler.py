"""
Webhook handler for AI Market Insight Bot.
Handles payment webhooks from NOWPayments.
"""

import logging
import json
from aiohttp import web
from typing import Optional

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handler for payment webhooks.
    
    Provides:
    - NOWPayments webhook endpoint
    - Signature verification
    - Payment confirmation processing
    - Subscription activation
    """
    
    def __init__(
        self,
        payment_service,
        subscription_service
    ):
        """
        Initialize webhook handler.
        
        Args:
            payment_service: PaymentService instance
            subscription_service: SubscriptionService instance
        """
        self.payment_service = payment_service
        self.subscription_service = subscription_service
        
        logger.info("WebhookHandler initialized")
    
    async def handle_nowpayments_webhook(self, request: web.Request) -> web.Response:
        """
        Handle NOWPayments IPN callback.
        
        Args:
            request: aiohttp Request object
            
        Returns:
            aiohttp Response
        """
        try:
            # Get signature from header
            signature = request.headers.get('x-nowpayments-sig', '')
            
            if not signature:
                logger.warning("Webhook received without signature")
                return web.Response(status=400, text="Missing signature")
            
            # Get raw payload
            payload = await request.text()
            
            # Verify signature
            is_valid = await self.payment_service.verify_webhook_signature(
                payload,
                signature
            )
            
            if not is_valid:
                logger.error("Invalid webhook signature")
                return web.Response(status=401, text="Invalid signature")
            
            # Parse webhook data
            try:
                webhook_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook payload: {e}")
                return web.Response(status=400, text="Invalid JSON")
            
            # Log webhook receipt
            logger.info(f"Received webhook: {webhook_data.get('payment_status')} for invoice {webhook_data.get('invoice_id')}")
            
            # Process webhook
            success = await self.payment_service.process_payment_webhook(webhook_data)
            
            if not success:
                logger.error("Failed to process webhook")
                return web.Response(status=500, text="Processing failed")
            
            # If payment is confirmed, activate subscription
            payment_status = webhook_data.get('payment_status')
            
            if payment_status == 'finished':
                await self._activate_subscription_from_webhook(webhook_data)
            
            return web.Response(status=200, text="OK")
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return web.Response(status=500, text="Internal error")
    
    async def _activate_subscription_from_webhook(
        self,
        webhook_data: dict
    ) -> bool:
        """
        Activate subscription after payment confirmation.
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            True if successful
        """
        try:
            invoice_id = webhook_data.get('invoice_id')
            
            if not invoice_id:
                logger.error("Webhook missing invoice_id")
                return False
            
            # Find payment record
            payment = await self.payment_service.payment_repo.find_by_invoice_id(
                str(invoice_id)
            )
            
            if not payment:
                logger.error(f"Payment not found for invoice: {invoice_id}")
                return False
            
            # Activate subscription
            success = await self.subscription_service.activate_subscription(
                subscription_id=payment['subscription_id'],
                payment_id=payment['payment_id'],
                months=1  # Default to 1 month
            )
            
            if success:
                logger.info(f"Activated subscription {payment['subscription_id']} from webhook")
                # Confirmation notification is sent automatically by SubscriptionService

            return success
            
        except Exception as e:
            logger.error(f"Error activating subscription from webhook: {e}", exc_info=True)
            return False
    
    async def health_check(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.
        
        Args:
            request: aiohttp Request object
            
        Returns:
            aiohttp Response
        """
        return web.Response(status=200, text="OK")


async def create_webhook_server(
    payment_service,
    subscription_service,
    host: str = '0.0.0.0',
    port: int = 8080
):
    """
    Create and start webhook server.
    
    Args:
        payment_service: PaymentService instance
        subscription_service: SubscriptionService instance
        host: Server host
        port: Server port
        
    Returns:
        Tuple of (app, runner, site)
    """
    # Create handler
    handler = WebhookHandler(payment_service, subscription_service)
    
    # Create aiohttp application
    app = web.Application()
    
    # Add routes
    app.router.add_post('/webhook/payment', handler.handle_nowpayments_webhook)
    app.router.add_get('/health', handler.health_check)
    
    # Create runner
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Create site
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"✅ Webhook server started on {host}:{port}")
    logger.info(f"   - POST /webhook/payment - NOWPayments webhook")
    logger.info(f"   - GET  /health - Health check")
    
    return app, runner, site


async def shutdown_webhook_server(runner):
    """
    Shutdown webhook server.
    
    Args:
        runner: aiohttp AppRunner instance
    """
    try:
        await runner.cleanup()
        logger.info("✅ Webhook server shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down webhook server: {e}", exc_info=True)

