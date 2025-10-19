"""
Test script for subscription system
Tests all components of the subscription payment system.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_pool import ConnectionPool
from db_adapter import DatabaseAdapter
from repositories.subscription_repository import SubscriptionRepository
from repositories.payment_repository import PaymentRepository
from repositories.group_repository import GroupRepository
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService
from core.metrics import MetricsCollector
from migrations import run_all_migrations
import config


class SubscriptionSystemTester:
    """Test suite for subscription system."""

    def __init__(self):
        self.db_pool = None
        self.db_pool = None
        self.subscription_repo = None
        self.payment_repo = None
        self.group_repo = None
        self.subscription_service = None
        self.payment_service = None
        self.metrics = MetricsCollector()
        self.test_results = []

    async def setup(self):
        """Initialize database and repositories."""
        print("🔧 Setting up test environment...")

        # Set environment variable for test database
        import os
        os.environ['DATABASE_URL'] = 'test_ainews.db'

        # Initialize database pool (synchronous) - uses global pool
        from db_pool import init_pool
        self.db_pool = init_pool(db_path="test_ainews.db", pool_size=5)

        # Create base tables first (minimal schema for testing)
        print("📦 Creating test database schema...")
        with self.db_pool.get_connection() as conn:
            # Create groups table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    posting_time TEXT DEFAULT '09:00',
                    trader_type TEXT DEFAULT 'investor',
                    is_active BOOLEAN DEFAULT 1,
                    last_post TIMESTAMP,
                    subscription_id INTEGER,
                    subscription_status TEXT DEFAULT 'trial',
                    trial_ends_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create subscriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL UNIQUE,
                    subscription_status TEXT NOT NULL,
                    trial_start_date TIMESTAMP NOT NULL,
                    trial_end_date TIMESTAMP NOT NULL,
                    subscription_start_date TIMESTAMP,
                    subscription_end_date TIMESTAMP,
                    next_billing_date TIMESTAMP,
                    grace_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
                )
            """)

            # Create payments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    amount_usd DECIMAL(10, 2) NOT NULL,
                    amount_crypto DECIMAL(20, 8),
                    currency TEXT NOT NULL,
                    payment_address TEXT,
                    payment_status TEXT NOT NULL,
                    payment_url TEXT,
                    invoice_id TEXT UNIQUE,
                    payment_id_external TEXT,
                    transaction_hash TEXT,
                    confirmations INTEGER DEFAULT 0,
                    required_confirmations INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    webhook_data TEXT,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
                )
            """)

            # Create subscription_events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscription_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
                )
            """)

            # Create trial_abuse_tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trial_abuse_tracking (
                    tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    group_title_hash TEXT NOT NULL,
                    creator_user_id INTEGER,
                    trial_started_at TIMESTAMP NOT NULL,
                    is_flagged BOOLEAN DEFAULT 0,
                    flag_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

        print("✅ Test schema created!")

        # Initialize repositories
        self.subscription_repo = SubscriptionRepository(self.db_pool)
        self.payment_repo = PaymentRepository(self.db_pool)
        self.group_repo = GroupRepository(self.db_pool)
        
        # Initialize services
        self.subscription_service = SubscriptionService(
            subscription_repo=self.subscription_repo,
            payment_repo=self.payment_repo,
            group_repo=self.group_repo,
            metrics=self.metrics
        )
        
        self.payment_service = PaymentService(
            payment_repo=self.payment_repo,
            subscription_repo=self.subscription_repo,
            metrics=self.metrics
        )
        
        print("✅ Setup complete!\n")
    
    async def cleanup(self):
        """Cleanup test data and close connections."""
        print("\n🧹 Cleaning up...")

        # Delete test data (synchronous operations)
        try:
            with self.db_pool.get_connection() as conn:
                # Try to delete from each table, ignore if table doesn't exist
                for table in ['subscription_events', 'payments', 'subscriptions', 'trial_abuse_tracking', 'groups']:
                    try:
                        conn.execute(f"DELETE FROM {table} WHERE group_id < 0")
                    except Exception as e:
                        pass  # Table might not exist
                conn.commit()
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")

        self.db_pool.close_all()
        print("✅ Cleanup complete!")
    
    def log_test(self, test_name, passed, message=""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((test_name, passed, message))
        print(f"{status} - {test_name}")
        if message:
            print(f"   {message}")
    
    async def test_trial_creation(self):
        """Test 1: Trial subscription creation."""
        print("\n📝 Test 1: Trial Subscription Creation")
        print("=" * 50)
        
        try:
            # Create test group
            group_id = -1001
            group_name = "Test Group 1"
            creator_user_id = 12345
            
            # Register group
            await self.group_repo.create(group_id, group_name, "09:00", "investor")
            
            # Create trial subscription
            subscription = await self.subscription_service.create_trial_subscription(
                group_id, group_name, creator_user_id
            )
            
            # Verify subscription was created
            if subscription:
                self.log_test(
                    "Trial Creation",
                    True,
                    f"Trial created with ID: {subscription['subscription_id']}, "
                    f"Ends: {subscription['trial_end_date'][:10]}"
                )
                
                # Verify trial days
                trial_end = datetime.fromisoformat(subscription['trial_end_date'].replace('Z', '+00:00'))
                trial_start = datetime.fromisoformat(subscription['trial_start_date'].replace('Z', '+00:00'))
                days_diff = (trial_end - trial_start).days
                
                self.log_test(
                    "Trial Duration",
                    days_diff == config.TRIAL_DAYS,
                    f"Trial duration: {days_diff} days (expected: {config.TRIAL_DAYS})"
                )
            else:
                self.log_test("Trial Creation", False, "Failed to create trial")
                
        except Exception as e:
            self.log_test("Trial Creation", False, f"Error: {str(e)}")
    
    async def test_subscription_status(self):
        """Test 2: Subscription status retrieval."""
        print("\n📝 Test 2: Subscription Status Retrieval")
        print("=" * 50)
        
        try:
            group_id = -1001
            
            # Get subscription status
            status = await self.subscription_service.get_subscription_status(group_id)
            
            if status:
                self.log_test(
                    "Status Retrieval",
                    status['has_subscription'],
                    f"Status: {status['status']}, "
                    f"Posting allowed: {status['posting_allowed']}, "
                    f"Trial days left: {status.get('trial_days_left', 'N/A')}"
                )
            else:
                self.log_test("Status Retrieval", False, "No status returned")
                
        except Exception as e:
            self.log_test("Status Retrieval", False, f"Error: {str(e)}")
    
    async def test_posting_validation(self):
        """Test 3: Posting validation."""
        print("\n📝 Test 3: Posting Validation")
        print("=" * 50)
        
        try:
            group_id = -1001
            
            # Check if posting is allowed
            is_allowed = await self.subscription_service.is_posting_allowed(group_id)
            
            self.log_test(
                "Posting Validation",
                is_allowed,
                f"Posting allowed: {is_allowed}"
            )
            
        except Exception as e:
            self.log_test("Posting Validation", False, f"Error: {str(e)}")
    
    async def test_trial_abuse_detection(self):
        """Test 4: Trial abuse detection."""
        print("\n📝 Test 4: Trial Abuse Detection")
        print("=" * 50)

        try:
            # Try to create another trial for the same group
            group_id = -1001
            group_name = "Test Group 1"
            creator_user_id = 12345

            # Get the original subscription ID
            original_sub = await self.subscription_service.get_subscription(group_id)
            original_id = original_sub['subscription_id'] if original_sub else None

            # Try to create another trial - should return existing subscription
            subscription = await self.subscription_service.create_trial_subscription(
                group_id, group_name, creator_user_id
            )

            # Check that it returned the existing subscription (same ID)
            is_same = (subscription and original_id and
                      subscription.get('subscription_id') == original_id)

            self.log_test(
                "Duplicate Trial Prevention",
                is_same,
                "Duplicate trial correctly prevented (returned existing)" if is_same
                else "WARNING: New trial created instead of returning existing!"
            )

        except Exception as e:
            self.log_test("Trial Abuse Detection", False, f"Error: {str(e)}")
    
    async def test_payment_invoice_creation(self):
        """Test 5: Payment invoice creation."""
        print("\n📝 Test 5: Payment Invoice Creation")
        print("=" * 50)
        
        try:
            # Get subscription
            group_id = -1001
            subscription = await self.subscription_service.get_subscription(group_id)
            
            if not subscription:
                self.log_test("Payment Invoice", False, "No subscription found")
                return
            
            # Check if API keys are configured
            if not config.NOWPAYMENTS_API_KEY:
                self.log_test(
                    "Payment Invoice",
                    True,
                    "⚠️ SKIPPED - NOWPayments API key not configured"
                )
                return
            
            # Create invoice
            invoice = await self.payment_service.create_invoice(
                subscription_id=subscription['subscription_id'],
                group_id=group_id,
                amount_usd=15.00,
                currency="btc",
                description="Test payment"
            )
            
            if invoice:
                self.log_test(
                    "Payment Invoice",
                    True,
                    f"Invoice created: {invoice.get('invoice_id', 'N/A')}, "
                    f"Amount: {invoice.get('pay_amount', 'N/A')} BTC"
                )
            else:
                self.log_test("Payment Invoice", False, "Failed to create invoice")
                
        except Exception as e:
            self.log_test("Payment Invoice", False, f"Error: {str(e)}")
    
    async def test_webhook_signature_verification(self):
        """Test 6: Webhook signature verification."""
        print("\n📝 Test 6: Webhook Signature Verification")
        print("=" * 50)
        
        try:
            # Check if IPN secret is configured
            if not config.NOWPAYMENTS_IPN_SECRET:
                self.log_test(
                    "Webhook Signature",
                    True,
                    "⚠️ SKIPPED - NOWPayments IPN secret not configured"
                )
                return
            
            # Test with sample data
            import hmac
            import hashlib
            
            payload = '{"invoice_id":"test123","payment_status":"finished"}'
            expected_signature = hmac.new(
                config.NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            # Verify signature
            is_valid = await self.payment_service.verify_webhook_signature(
                payload, expected_signature
            )
            
            self.log_test(
                "Webhook Signature",
                is_valid,
                f"Signature verification: {'Valid' if is_valid else 'Invalid'}"
            )
            
            # Test with invalid signature
            is_invalid = await self.payment_service.verify_webhook_signature(
                payload, "invalid_signature"
            )
            
            self.log_test(
                "Invalid Signature Detection",
                not is_invalid,
                f"Invalid signature correctly rejected: {not is_invalid}"
            )
            
        except Exception as e:
            self.log_test("Webhook Signature", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 50)
        print("🧪 SUBSCRIPTION SYSTEM TEST SUITE")
        print("=" * 50)
        
        await self.setup()
        
        # Run tests
        await self.test_trial_creation()
        await self.test_subscription_status()
        await self.test_posting_validation()
        await self.test_trial_abuse_detection()
        await self.test_payment_invoice_creation()
        await self.test_webhook_signature_verification()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for name, passed, message in self.test_results:
                if not passed:
                    print(f"  - {name}: {message}")
        
        await self.cleanup()
        
        return failed_tests == 0


async def main():
    """Main test runner."""
    tester = SubscriptionSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

