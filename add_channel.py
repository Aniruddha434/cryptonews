#!/usr/bin/env python3
"""
Add a Telegram channel to the database for automated posting.
Channels are different from groups - they don't support commands.
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def add_channel(channel_id: int, channel_name: str, trial_days: int = 15):
    """Add a channel to the database with a subscription."""
    # Connect to database
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if channel already exists
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (channel_id,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"\n⚠️  Channel {channel_id} already exists in database")
            print(f"📱 Name: {existing['group_name']}")
            print(f"📌 Status: {existing['subscription_status']}")
            print("\n💡 Use: python check_subscription.py <channel_id> to view details")
            return
        
        now = datetime.now()
        end_date = now + timedelta(days=trial_days)
        
        # Add channel to groups table
        cursor.execute("""
            INSERT INTO groups (
                group_id,
                group_name,
                subscription_status,
                is_active,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            channel_id,
            channel_name,
            'active',
            1,
            now.isoformat(),
            now.isoformat()
        ))
        
        # Create subscription
        cursor.execute("""
            INSERT INTO subscriptions (
                group_id,
                subscription_status,
                trial_start_date,
                trial_end_date,
                subscription_start_date,
                subscription_end_date,
                next_billing_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel_id,
            'active',
            now.isoformat(),
            end_date.isoformat(),
            now.isoformat(),
            end_date.isoformat(),
            (end_date - timedelta(days=7)).isoformat(),
            now.isoformat(),
            now.isoformat()
        ))
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ CHANNEL ADDED SUCCESSFULLY")
        print("="*60)
        print(f"\n📱 Channel ID: {channel_id}")
        print(f"📱 Channel Name: {channel_name}")
        print(f"📌 Status: ACTIVE")
        print(f"⏰ Valid Until: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Trial Period: {trial_days} days")
        print("\n🚀 Bot will now post to this channel!")
        print("\n" + "="*60)
        print("\n💡 IMPORTANT:")
        print("   1. Make sure the bot is added to your channel as an ADMIN")
        print("   2. The bot needs 'Post Messages' permission")
        print("   3. To get your channel ID, forward a message from the channel")
        print("      to @userinfobot on Telegram")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error adding channel: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("\n📖 USAGE:")
        print("   python add_channel.py <channel_id> <channel_name> [trial_days]")
        print("\n📝 EXAMPLES:")
        print('   python add_channel.py -1001234567890 "My Crypto Channel" 15')
        print('   python add_channel.py -1001234567890 "Daily Amazon Deals" 30')
        print("\n💡 HOW TO GET CHANNEL ID:")
        print("   1. Forward any message from your channel to @userinfobot")
        print("   2. The bot will show you the channel ID")
        print("   3. Channel IDs are negative numbers starting with -100")
        print("\n💡 IMPORTANT:")
        print("   • Add the bot to your channel as an ADMIN first")
        print("   • Give it 'Post Messages' permission")
        print("   • Channels don't support commands like /start or /register")
        print("   • The bot will only POST to channels, not respond to messages")
        return
    
    try:
        channel_id = int(sys.argv[1])
        channel_name = sys.argv[2]
        trial_days = int(sys.argv[3]) if len(sys.argv) >= 4 else 15
        
        # Validate channel ID format
        if channel_id >= 0:
            print("\n❌ Error: Channel ID must be a negative number")
            print("💡 Telegram channel IDs start with -100")
            print("   Example: -1001234567890")
            return
        
        if not channel_name:
            print("\n❌ Error: Channel name cannot be empty")
            return
        
        add_channel(channel_id, channel_name, trial_days)
        
    except ValueError:
        print("\n❌ Error: Invalid channel ID. Must be a number.")
        print("💡 Example: -1001234567890")

if __name__ == "__main__":
    main()

