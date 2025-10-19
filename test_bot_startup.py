"""
Quick test to verify bot components load correctly.
"""

import sys
import asyncio

async def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    try:
        from bot import EnterpriseBot
        print("✅ EnterpriseBot imported")
        
        from handlers import UserHandlers, AdminHandlers
        print("✅ Handlers imported")
        
        from services import NewsService, UserService, AnalyticsService, SchedulerService
        print("✅ Services imported")
        
        from core import init_container
        print("✅ Core components imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_initialization():
    """Test bot initialization."""
    print("\nTesting bot initialization...")
    
    try:
        from bot import EnterpriseBot
        
        bot = EnterpriseBot()
        print("✅ Bot instance created")
        
        await bot.initialize()
        print("✅ Services initialized")
        
        print("\n✅ Bot initialization successful!")
        
        # Cleanup
        from core import shutdown_container
        await shutdown_container()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("=" * 50)
    print("BOT STARTUP TEST")
    print("=" * 50)
    
    # Test imports
    if not await test_imports():
        sys.exit(1)
    
    # Test initialization
    if not await test_bot_initialization():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)
    print("\nYour bot is ready to run with: python bot.py")

if __name__ == "__main__":
    asyncio.run(main())

