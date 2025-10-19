"""
Payment repository for AI Market Insight Bot.
Handles all payment-related database operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PaymentRepository(BaseRepository):
    """
    Repository for payment data operations.
    
    Provides methods for:
    - Payment creation and retrieval
    - Payment status tracking
    - Invoice management
    - Transaction history
    """
    
    async def find_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        Find payment by ID.
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Payment data dictionary or None
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            WHERE payment_id = ?
        """
        
        return await self.execute_query(query, (payment_id,), fetch_one=True)
    
    async def find_by_invoice_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Find payment by invoice ID.
        
        Args:
            invoice_id: NOWPayments invoice ID
            
        Returns:
            Payment data dictionary or None
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            WHERE invoice_id = ?
        """
        
        return await self.execute_query(query, (invoice_id,), fetch_one=True)
    
    async def find_by_subscription_id(self, subscription_id: int) -> List[Dict[str, Any]]:
        """
        Find all payments for a subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            List of payment dictionaries
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            WHERE subscription_id = ?
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, (subscription_id,), fetch_all=True)
    
    async def find_by_group_id(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Find all payments for a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List of payment dictionaries
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            WHERE group_id = ?
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, (group_id,), fetch_all=True)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """
        Get all payments.
        
        Returns:
            List of payment dictionaries
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create new payment.
        
        Args:
            data: Payment data
            
        Returns:
            Created payment data or None
        """
        query = """
            INSERT INTO payments (
                subscription_id, group_id, amount_usd, amount_crypto,
                currency, payment_address, payment_status, payment_url,
                invoice_id, payment_id_external, transaction_hash,
                confirmations, required_confirmations, created_at,
                confirmed_at, expires_at, webhook_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(
                query,
                (
                    data['subscription_id'],
                    data['group_id'],
                    data['amount_usd'],
                    data.get('amount_crypto'),
                    data['currency'],
                    data.get('payment_address'),
                    data['payment_status'],
                    data.get('payment_url'),
                    data.get('invoice_id'),
                    data.get('payment_id_external'),
                    data.get('transaction_hash'),
                    data.get('confirmations', 0),
                    data.get('required_confirmations', 1),
                    now,
                    data.get('confirmed_at'),
                    data.get('expires_at'),
                    data.get('webhook_data')
                )
            )
            
            self.logger.info(f"Created payment for subscription: {data['subscription_id']}")
            
            # Return the created payment
            if data.get('invoice_id'):
                return await self.find_by_invoice_id(data['invoice_id'])
            else:
                # Find by subscription_id and created_at
                payments = await self.find_by_subscription_id(data['subscription_id'])
                return payments[0] if payments else None
            
        except Exception as e:
            self.logger.error(f"Failed to create payment: {e}")
            return None
    
    async def update(self, payment_id: int, data: Dict[str, Any]) -> bool:
        """
        Update payment data.
        
        Args:
            payment_id: Payment ID
            data: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        fields = []
        values = []
        
        allowed_fields = [
            'amount_crypto', 'payment_address', 'payment_status',
            'payment_id_external', 'transaction_hash', 'confirmations',
            'required_confirmations', 'confirmed_at', 'webhook_data'
        ]
        
        for key, value in data.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        query = f"UPDATE payments SET {', '.join(fields)} WHERE payment_id = ?"
        values.append(payment_id)
        
        try:
            await self.execute_query(query, tuple(values))
            self.logger.info(f"Updated payment: {payment_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update payment {payment_id}: {e}")
            return False
    
    async def delete(self, payment_id: int) -> bool:
        """
        Delete payment.
        
        Args:
            payment_id: Payment ID
            
        Returns:
            True if successful
        """
        query = "DELETE FROM payments WHERE payment_id = ?"
        
        try:
            await self.execute_query(query, (payment_id,))
            self.logger.info(f"Deleted payment: {payment_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete payment {payment_id}: {e}")
            return False
    
    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Find payments by status.
        
        Args:
            status: Payment status
            
        Returns:
            List of payment dictionaries
        """
        query = """
            SELECT payment_id, subscription_id, group_id, amount_usd,
                   amount_crypto, currency, payment_address, payment_status,
                   payment_url, invoice_id, payment_id_external, transaction_hash,
                   confirmations, required_confirmations, created_at, confirmed_at,
                   expires_at, webhook_data
            FROM payments
            WHERE payment_status = ?
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, (status,), fetch_all=True)
    
    async def find_pending_payments(self) -> List[Dict[str, Any]]:
        """
        Find all pending payments.
        
        Returns:
            List of payment dictionaries
        """
        return await self.find_by_status('pending')
    
    async def find_confirmed_payments(self) -> List[Dict[str, Any]]:
        """
        Find all confirmed payments.
        
        Returns:
            List of payment dictionaries
        """
        return await self.find_by_status('finished')
    
    async def count_by_status(self, status: str) -> int:
        """
        Count payments by status.
        
        Args:
            status: Payment status
            
        Returns:
            Payment count
        """
        query = "SELECT COUNT(*) as count FROM payments WHERE payment_status = ?"
        result = await self.execute_query(query, (status,), fetch_one=True)
        return result['count'] if result else 0
    
    async def get_total_revenue(self) -> float:
        """
        Get total revenue from confirmed payments.
        
        Returns:
            Total revenue in USD
        """
        query = """
            SELECT SUM(amount_usd) as total
            FROM payments
            WHERE payment_status = 'finished'
        """
        result = await self.execute_query(query, fetch_one=True)
        return float(result['total']) if result and result['total'] else 0.0

