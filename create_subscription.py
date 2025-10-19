#!/usr/bin/env python3
"""
Create a subscription for a group.
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def create_subscription(group_id: int, days: int = 15):
    """Create a new subscription for a group."""
    # Connect to database
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if group exists
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            print(f"\n❌ Group {group_id} not found in database")
            print("💡 Use /setup command in the Telegram group first")
            return
        
        # Check if subscription already exists
        cursor.execute("SELECT * FROM subscriptions WHERE group_id = ?", (group_id,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"\n⚠️  Subscription already exists for group {group_id}")
            print("💡 Use: python check_subscription.py <group_id> extend <days>")
            return
        
        # Create subscription
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
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
            group_id,
            'active',
            now.isoformat(),
            end_date.isoformat(),
            now.isoformat(),
            end_date.isoformat(),
            (end_date - timedelta(days=7)).isoformat(),
            now.isoformat(),
            now.isoformat()
        ))
        
        # Update group
        cursor.execute("""
            UPDATE groups 
            SET subscription_status = ?,
                is_active = ?,
                updated_at = ?
            WHERE group_id = ?
        """, ('active', 1, now.isoformat(), group_id))
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ SUBSCRIPTION CREATED SUCCESSFULLY")
        print("="*60)
        print(f"\n📱 Group ID: {group_id}")
        print(f"📱 Group Name: {group['group_name']}")
        print(f"📌 Status: ACTIVE")
        print(f"⏰ Valid Until: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Duration: {days} days")
        print("\n🚀 Posting is now ENABLED for this group!")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error creating subscription: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("\n📖 USAGE:")
        print("   python create_subscription.py <group_id> [days]")
        print("\n📝 EXAMPLES:")
        print("   python create_subscription.py -1002885984549")
        print("   python create_subscription.py -1002885984549 60")
        print("\n💡 Default trial period: 15 days")
        return

    group_id = int(sys.argv[1])
    days = int(sys.argv[2]) if len(sys.argv) >= 3 else 15
    
    create_subscription(group_id, days)

if __name__ == "__main__":
    main()

