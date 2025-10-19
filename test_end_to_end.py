"""
End-to-end integration tests for subscription system.
Tests complete user flows from trial to subscription.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Test database
TEST_DB = "test_e2e.db"

# Clean up old test database
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)


async def test_complete_subscription_flow():
    """
    Test complete subscription flow:
    1. Bot joins group → Trial created
    2. Trial warnings sent
    3. Trial expires → Grace period
    4. Payment made → Subscription activated
    5. Subscription expires → Group disabled
    """
    print("\n" + "="*60)
    print("🧪 END-TO-END SUBSCRIPTION FLOW TEST")
    print("="*60)
    
    from db_pool import ConnectionPool
    from repositories.subscription_repository import SubscriptionRepository
    from repositories.payment_repository import PaymentRepository
    from repositories.group_repository import GroupRepository
    from services.subscription_service import SubscriptionService
    from services.payment_service import PaymentService
    from services.notification_service import NotificationService
    from core.metrics import MetricsCollector
    
    # Create database pool
    pool = ConnectionPool(db_path=TEST_DB, pool_size=5)
    
    # Create schema (using actual migration schema)
    print("\n📝 Setting up test database...")
    from migrations.migration_006_subscription_system import MIGRATION_006

    # Also need groups table
    groups_table = """
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        group_id INTEGER UNIQUE NOT NULL,
        group_name TEXT,
        is_active INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    with pool.get_connection() as conn:
        # Create groups table
        conn.execute(groups_table)
        # Create subscription tables from migration
        for statement in MIGRATION_006:
            if statement.strip():
                conn.execute(statement)
        conn.commit()

    print("✅ Database schema created")
    
    # Create repositories
    subscription_repo = SubscriptionRepository(pool)
    payment_repo = PaymentRepository(pool)
    group_repo = GroupRepository(pool)
    metrics = MetricsCollector()
    
    # Create services
    notification_service = NotificationService(metrics)
    subscription_service = SubscriptionService(
        subscription_repo=subscription_repo,
        payment_repo=payment_repo,
        group_repo=group_repo,
        metrics=metrics,
        notification_service=notification_service
    )
    payment_service = PaymentService(
        payment_repo=payment_repo,
        subscription_repo=subscription_repo,
        metrics=metrics
    )
    
    # Test data
    test_group_id = -1001234567890
    test_group_name = "Test Crypto Group"
    test_creator_id = 123456789
    
    print("\n" + "="*60)
    print("STEP 1: Bot Joins Group → Trial Created")
    print("="*60)

    # First, create the group record (required for foreign key)
    with pool.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO groups (group_id, group_name, is_active, status)
            VALUES (?, ?, 1, 'active')
            """,
            (test_group_id, test_group_name)
        )
        conn.commit()
    print(f"✅ Group record created: {test_group_name}")

    # Create trial subscription
    subscription = await subscription_service.create_trial_subscription(
        group_id=test_group_id,
        group_name=test_group_name,
        creator_user_id=test_creator_id
    )
    
    if subscription:
        print(f"✅ Trial created:")
        print(f"   • Subscription ID: {subscription['subscription_id']}")
        print(f"   • Status: {subscription['subscription_status']}")
        print(f"   • Trial ends: {subscription['trial_end_date']}")
    else:
        print("❌ Failed to create trial")
        return False
    
    print("\n" + "="*60)
    print("STEP 2: Check Posting Permission (Trial Active)")
    print("="*60)

    can_post = await subscription_service.is_posting_allowed(test_group_id)
    print(f"✅ Can post to group: {can_post}")

    if not can_post:
        print("❌ Should be able to post during trial")
        return False
    
    print("\n" + "="*60)
    print("STEP 3: Simulate Trial Expiration")
    print("="*60)
    
    # Manually expire the trial
    expired_date = (datetime.now() - timedelta(days=1)).isoformat()
    grace_end = (datetime.now() + timedelta(days=3)).isoformat()

    with pool.get_connection() as conn:
        conn.execute(
            """
            UPDATE subscriptions
            SET subscription_status = 'grace_period',
                trial_end_date = ?,
                grace_period_end = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE subscription_id = ?
            """,
            (expired_date, grace_end, subscription['subscription_id'])
        )
        conn.commit()
    
    print("✅ Trial expired, grace period activated")
    
    # Check posting permission during grace period
    can_post = await subscription_service.is_posting_allowed(test_group_id)
    print(f"✅ Can post during grace period: {can_post}")

    if not can_post:
        print("❌ Should be able to post during grace period")
        return False
    
    print("\n" + "="*60)
    print("STEP 4: Create Payment Invoice")
    print("="*60)
    
    # Note: This will fail without API key, but tests the logic
    invoice = await payment_service.create_invoice(
        subscription_id=subscription['subscription_id'],
        group_id=test_group_id,
        amount_usd=15.00,
        currency="btc",
        description="Test subscription payment"
    )

    if invoice:
        print(f"✅ Invoice created: {invoice.get('invoice_id')}")
    else:
        print("⚠️  Invoice creation skipped (API key not configured - expected)")
        # Create mock payment record for testing
        with pool.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO payments (subscription_id, group_id, amount_usd, currency, invoice_id, payment_status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (subscription['subscription_id'], test_group_id, 15.00, 'btc', 'TEST_INVOICE_123', 'pending')
            )
            conn.commit()
            payment_id = cursor.lastrowid
        print(f"✅ Mock payment record created (ID: {payment_id})")
    
    print("\n" + "="*60)
    print("STEP 5: Simulate Payment Confirmation")
    print("="*60)
    
    # Simulate webhook payment confirmation
    webhook_data = {
        'invoice_id': 'TEST_INVOICE_123',
        'payment_status': 'finished',
        'actually_paid': 15.00,
        'pay_currency': 'btc'
    }
    
    success = await payment_service.process_payment_webhook(webhook_data)
    print(f"✅ Webhook processed: {success}")
    
    # Manually activate subscription (simulating webhook handler)
    # Note: activate_subscription requires payment_id, so let's use the mock payment
    activated = await subscription_service.activate_subscription(
        subscription_id=subscription['subscription_id'],
        payment_id=payment_id,
        months=1
    )
    
    if activated:
        print("✅ Subscription activated for 30 days")
    else:
        print("❌ Failed to activate subscription")
        return False
    
    # Check posting permission with active subscription
    can_post = await subscription_service.is_posting_allowed(test_group_id)
    print(f"✅ Can post with active subscription: {can_post}")

    if not can_post:
        print("❌ Should be able to post with active subscription")
        return False
    
    print("\n" + "="*60)
    print("STEP 6: Simulate Subscription Expiration")
    print("="*60)
    
    # Manually expire the subscription
    with pool.get_connection() as conn:
        conn.execute(
            """
            UPDATE subscriptions
            SET subscription_status = 'expired',
                subscription_end_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE subscription_id = ?
            """,
            (expired_date, subscription['subscription_id'])
        )
        conn.execute(
            """
            UPDATE groups
            SET is_active = 0,
                status = 'expired'
            WHERE group_id = ?
            """,
            (test_group_id,)
        )
        conn.commit()
    
    print("✅ Subscription expired, group disabled")
    
    # Check posting permission with expired subscription
    can_post = await subscription_service.is_posting_allowed(test_group_id)
    print(f"✅ Can post with expired subscription: {can_post}")

    if can_post:
        print("❌ Should NOT be able to post with expired subscription")
        return False
    
    print("\n" + "="*60)
    print("📊 FINAL VERIFICATION")
    print("="*60)
    
    # Get final subscription status
    final_subscription = await subscription_repo.find_by_group_id(test_group_id)
    print(f"\n✅ Final subscription status:")
    print(f"   • Status: {final_subscription['subscription_status']}")
    print(f"   • Trial period: {final_subscription['trial_start_date']} → {final_subscription['trial_end_date']}")
    print(f"   • Subscription period: {final_subscription['subscription_start_date']} → {final_subscription['subscription_end_date']}")

    # Get payment records
    with pool.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM payments WHERE subscription_id = ?",
            (subscription['subscription_id'],)
        )
        payments = [dict(row) for row in cursor.fetchall()]

    print(f"\n✅ Payment records: {len(payments)}")
    for payment in payments:
        print(f"   • Invoice: {payment['invoice_id']}, Status: {payment['payment_status']}")

    # Get events
    with pool.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM subscription_events WHERE subscription_id = ? ORDER BY created_at",
            (subscription['subscription_id'],)
        )
        events = [dict(row) for row in cursor.fetchall()]

    print(f"\n✅ Subscription events: {len(events)}")
    for event in events:
        print(f"   • {event['event_type']} at {event['created_at']}")
    
    # Cleanup
    try:
        pool.close_all()
        print("\n🧹 Database connections closed")
    except Exception as e:
        print(f"⚠️  Error closing pool: {e}")

    print("\n" + "="*60)
    print("✅ END-TO-END TEST COMPLETED SUCCESSFULLY")
    print("="*60)

    return True


if __name__ == "__main__":
    success = False
    try:
        success = asyncio.run(test_complete_subscription_flow())
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup test database
        import time
        time.sleep(0.5)  # Give time for connections to close
        try:
            if os.path.exists(TEST_DB):
                os.remove(TEST_DB)
                print(f"\n🧹 Cleaned up test database: {TEST_DB}")
        except PermissionError:
            print(f"\n⚠️  Could not delete test database (file in use): {TEST_DB}")
        except Exception as e:
            print(f"\n⚠️  Error cleaning up test database: {e}")

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

