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

    async def root_handler(self, request: web.Request) -> web.Response:
        """
        Root path handler - returns bot status page.

        Args:
            request: aiohttp Request object

        Returns:
            aiohttp Response with HTML status page
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crypto News Bot - Status</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 600px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                }
                h1 {
                    margin: 0 0 10px 0;
                    font-size: 2.5em;
                }
                .status {
                    display: inline-block;
                    background: #10b981;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    margin: 20px 0;
                }
                .info {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }
                .info-item {
                    margin: 10px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .label {
                    opacity: 0.8;
                }
                .value {
                    font-weight: bold;
                }
                a {
                    color: #60a5fa;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                .footer {
                    margin-top: 30px;
                    opacity: 0.7;
                    font-size: 0.9em;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Crypto News Bot</h1>
                <div class="status">✅ ONLINE</div>

                <div class="info">
                    <div class="info-item">
                        <span class="label">Service:</span>
                        <span class="value">Telegram Bot</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Mode:</span>
                        <span class="value">Real-time News (24/7)</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Status:</span>
                        <span class="value">Running</span>
                    </div>
                </div>

                <p>This is a Telegram bot service for AI-powered crypto news analysis and distribution.</p>

                <p><strong>Features:</strong></p>
                <ul>
                    <li>🔥 Real-time hot news monitoring</li>
                    <li>🤖 AI-powered market analysis</li>
                    <li>📊 Multi-group distribution</li>
                    <li>💳 Subscription management</li>
                </ul>

                <div class="footer">
                    <p>Powered by Google Gemini AI & CryptoPanic API</p>
                    <p><a href="/health">Health Check</a> | <a href="/webhook/payment">Payment Webhook</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')


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
    app.router.add_get('/', handler.root_handler)
    app.router.add_post('/webhook/payment', handler.handle_nowpayments_webhook)
    app.router.add_get('/health', handler.health_check)
    
    # Create runner
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Create site
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"✅ Webhook server started on {host}:{port}")
    logger.info(f"   - GET  / - Status page")
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
