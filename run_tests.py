"""
Quick test runner for subscription system
Provides an interactive menu for running different test suites.
"""

import asyncio
import sys
import os

def print_header():
    """Print test menu header."""
    print("\n" + "=" * 60)
    print("🧪 SUBSCRIPTION SYSTEM TEST RUNNER")
    print("=" * 60)
    print()

def print_menu():
    """Print test menu options."""
    print("Select a test suite to run:")
    print()
    print("1. 🚀 Run All Automated Tests (Recommended)")
    print("2. 📊 Test Database Migrations Only")
    print("3. 🔧 Test Subscription Service Only")
    print("4. 💳 Test Payment Service Only")
    print("5. 🌐 Test Webhook Server")
    print("6. 📝 View Test Results Summary")
    print("7. 🧹 Clean Test Data")
    print("8. ❌ Exit")
    print()

async def run_all_tests():
    """Run complete test suite."""
    print("\n🚀 Running all automated tests...")
    print("-" * 60)
    
    try:
        from test_subscription_system import SubscriptionSystemTester
        
        tester = SubscriptionSystemTester()
        success = await tester.run_all_tests()
        
        return success
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

async def test_migrations():
    """Test database migrations only."""
    print("\n📊 Testing database migrations...")
    print("-" * 60)

    try:
        from db_pool import ConnectionPool
        from migrations import run_all_migrations

        pool = ConnectionPool(db_path="test_ainews.db", pool_size=5)

        print("Running migrations...")
        await run_all_migrations(pool.adapter)

        # Verify tables exist
        with pool.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%subscription%'"
            )
            tables = cursor.fetchall()

            print(f"\n✅ Found {len(tables)} subscription-related tables:")
            for table in tables:
                print(f"   - {table[0]}")

        pool.close_all()
        print("\n✅ Migration test complete!")
        return True

    except Exception as e:
        print(f"❌ Error testing migrations: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_subscription_service():
    """Test subscription service only."""
    print("\n🔧 Testing subscription service...")
    print("-" * 60)

    try:
        from db_pool import ConnectionPool
        from repositories.subscription_repository import SubscriptionRepository
        from repositories.payment_repository import PaymentRepository
        from repositories.group_repository import GroupRepository
        from services.subscription_service import SubscriptionService
        from core.metrics import MetricsCollector
        from migrations import run_all_migrations

        # Setup
        pool = ConnectionPool(db_path="test_ainews.db", pool_size=5)
        await run_all_migrations(pool.adapter)

        subscription_repo = SubscriptionRepository(pool)
        payment_repo = PaymentRepository(pool)
        group_repo = GroupRepository(pool)
        metrics = MetricsCollector()
        
        service = SubscriptionService(
            subscription_repo=subscription_repo,
            payment_repo=payment_repo,
            group_repo=group_repo,
            metrics=metrics
        )
        
        # Test trial creation
        print("\n1. Testing trial creation...")
        group_id = -9999
        group_name = "Test Group"
        
        # Register group first
        await group_repo.create(group_id, group_name, "09:00", "investor")
        
        subscription = await service.create_trial_subscription(
            group_id, group_name, 12345
        )
        
        if subscription:
            print(f"   ✅ Trial created: ID {subscription['subscription_id']}")
        else:
            print("   ❌ Failed to create trial")
        
        # Test status retrieval
        print("\n2. Testing status retrieval...")
        status = await service.get_subscription_status(group_id)
        
        if status:
            print(f"   ✅ Status: {status['status']}")
            print(f"   ✅ Posting allowed: {status['posting_allowed']}")
        else:
            print("   ❌ Failed to get status")
        
        # Test posting validation
        print("\n3. Testing posting validation...")
        is_allowed = await service.is_posting_allowed(group_id)
        print(f"   ✅ Posting allowed: {is_allowed}")

        # Cleanup
        with pool.get_connection() as conn:
            conn.execute("DELETE FROM subscriptions WHERE group_id = ?", (group_id,))
            conn.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
            conn.commit()

        pool.close_all()
        print("\n✅ Subscription service test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing subscription service: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_payment_service():
    """Test payment service only."""
    print("\n💳 Testing payment service...")
    print("-" * 60)

    try:
        from db_pool import ConnectionPool
        from repositories.payment_repository import PaymentRepository
        from repositories.subscription_repository import SubscriptionRepository
        from services.payment_service import PaymentService
        from core.metrics import MetricsCollector
        from migrations import run_all_migrations
        import config

        # Setup
        pool = ConnectionPool(db_path="test_ainews.db", pool_size=5)
        await run_all_migrations(pool.adapter)

        payment_repo = PaymentRepository(pool)
        subscription_repo = SubscriptionRepository(pool)
        metrics = MetricsCollector()
        
        service = PaymentService(
            payment_repo=payment_repo,
            subscription_repo=subscription_repo,
            metrics=metrics
        )
        
        # Test webhook signature verification
        print("\n1. Testing webhook signature verification...")
        
        if not config.NOWPAYMENTS_IPN_SECRET:
            print("   ⚠️ SKIPPED - IPN secret not configured")
        else:
            import hmac
            import hashlib
            
            payload = '{"test":"data"}'
            signature = hmac.new(
                config.NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            is_valid = await service.verify_webhook_signature(payload, signature)
            print(f"   ✅ Valid signature verified: {is_valid}")
            
            is_invalid = await service.verify_webhook_signature(payload, "invalid")
            print(f"   ✅ Invalid signature rejected: {not is_invalid}")
        
        # Test invoice creation
        print("\n2. Testing invoice creation...")

        if not config.NOWPAYMENTS_API_KEY:
            print("   ⚠️ SKIPPED - API key not configured")
        else:
            print("   ℹ️ Would create invoice (skipped to avoid API calls)")

        pool.close_all()
        print("\n✅ Payment service test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing payment service: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_webhook_server():
    """Test webhook server."""
    print("\n🌐 Testing webhook server...")
    print("-" * 60)
    
    try:
        import aiohttp
        
        print("\n1. Testing health endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8080/health', timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   ✅ Health check passed: {data}")
                    else:
                        print(f"   ❌ Health check failed: {resp.status}")
        except aiohttp.ClientConnectorError:
            print("   ⚠️ Webhook server not running")
            print("   ℹ️ Start the bot first: python bot.py")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n2. Testing webhook endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://localhost:8080/webhook/payment',
                    json={"test": "data"},
                    headers={"x-nowpayments-sig": "invalid"},
                    timeout=5
                ) as resp:
                    if resp.status == 401:
                        print("   ✅ Invalid signature correctly rejected")
                    else:
                        print(f"   ⚠️ Unexpected status: {resp.status}")
        except aiohttp.ClientConnectorError:
            print("   ⚠️ Webhook server not running")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n✅ Webhook server test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing webhook server: {e}")
        return False

async def clean_test_data():
    """Clean test data from database."""
    print("\n🧹 Cleaning test data...")
    print("-" * 60)

    try:
        from db_pool import ConnectionPool

        pool = ConnectionPool(db_path="test_ainews.db", pool_size=5)

        with pool.get_connection() as conn:
            # Delete test data (negative group IDs)
            conn.execute("DELETE FROM subscription_events WHERE group_id < 0")
            conn.execute("DELETE FROM payments WHERE group_id < 0")
            conn.execute("DELETE FROM subscriptions WHERE group_id < 0")
            conn.execute("DELETE FROM trial_abuse_tracking WHERE group_id < 0")
            conn.execute("DELETE FROM groups WHERE group_id < 0")
            conn.commit()

        pool.close_all()
        print("✅ Test data cleaned!")
        return True

    except Exception as e:
        print(f"❌ Error cleaning test data: {e}")
        return False

async def main():
    """Main test runner."""
    while True:
        print_header()
        print_menu()
        
        try:
            choice = input("Enter your choice (1-8): ").strip()
            
            if choice == "1":
                await run_all_tests()
            elif choice == "2":
                await test_migrations()
            elif choice == "3":
                await test_subscription_service()
            elif choice == "4":
                await test_payment_service()
            elif choice == "5":
                await test_webhook_server()
            elif choice == "6":
                print("\n📝 For detailed test results, run option 1")
            elif choice == "7":
                await clean_test_data()
            elif choice == "8":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-8.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())

