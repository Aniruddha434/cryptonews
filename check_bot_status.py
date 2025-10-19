"""
Diagnostic script to check Telegram bot status and clear webhooks.
Run this to diagnose and fix the "Conflict: terminated by other getUpdates" error.
"""

import asyncio
import sys
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN

async def check_and_fix_bot():
    """Check bot status and clear any webhooks."""
    print("=" * 60)
    print("🔍 Telegram Bot Diagnostic Tool")
    print("=" * 60)
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        print("\n1️⃣ Checking bot information...")
        me = await bot.get_me()
        print(f"   ✅ Bot: @{me.username} ({me.first_name})")
        print(f"   ✅ Bot ID: {me.id}")
        
        # Check webhook status
        print("\n2️⃣ Checking webhook status...")
        webhook_info = await bot.get_webhook_info()
        
        if webhook_info.url:
            print(f"   ⚠️  WEBHOOK IS SET!")
            print(f"   URL: {webhook_info.url}")
            print(f"   Pending updates: {webhook_info.pending_update_count}")
            print(f"   Last error: {webhook_info.last_error_message or 'None'}")
            print(f"   Last error date: {webhook_info.last_error_date or 'None'}")
            
            # Delete webhook
            print("\n3️⃣ Deleting webhook...")
            success = await bot.delete_webhook(drop_pending_updates=True)
            if success:
                print("   ✅ Webhook deleted successfully!")
                print("   ✅ Pending updates dropped!")
            else:
                print("   ❌ Failed to delete webhook")
        else:
            print("   ✅ No webhook set (using polling mode)")
            print("   ✅ This is correct for your setup")
        
        # Check for updates (this will fail if another instance is running)
        print("\n4️⃣ Testing getUpdates (checking for conflicts)...")
        try:
            updates = await bot.get_updates(limit=1, timeout=5)
            print(f"   ✅ getUpdates successful! No conflicts detected.")
            print(f"   Pending updates: {len(updates)}")
        except Exception as e:
            if "Conflict" in str(e):
                print(f"   ❌ CONFLICT DETECTED!")
                print(f"   Error: {e}")
                print(f"\n   🔍 This means another bot instance is running!")
                print(f"   Possible causes:")
                print(f"   - Multiple Render services running the same bot")
                print(f"   - Old deployment still active")
                print(f"   - Bot running on another server/computer")
                print(f"\n   📋 Action Required:")
                print(f"   1. Go to Render dashboard: https://dashboard.render.com")
                print(f"   2. Check for multiple services with your bot")
                print(f"   3. Suspend/delete all except the current one")
            else:
                print(f"   ⚠️  Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Diagnostic complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_and_fix_bot())

