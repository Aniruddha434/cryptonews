#!/usr/bin/env python3
"""
Script to check and manage subscription status for testing.
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def check_subscription_status(group_id: int):
    """Check subscription status for a group."""
    # Connect to database
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get subscription
        cursor.execute("SELECT * FROM subscriptions WHERE group_id = ?", (group_id,))
        subscription = cursor.fetchone()

        if not subscription:
            print(f"\n❌ No subscription found for group {group_id}")
            print("\n💡 To create a trial subscription, use /setup command in the Telegram group")
            return

        # Get group info
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        
        print("\n" + "="*60)
        print(f"📊 SUBSCRIPTION STATUS FOR GROUP {group_id}")
        print("="*60)

        if group:
            print(f"\n📱 Group Name: {group['group_name'] if group['group_name'] else 'Unknown'}")

        print(f"\n🔖 Subscription ID: {subscription['subscription_id']}")
        print(f"📌 Status: {subscription['subscription_status'].upper() if subscription['subscription_status'] else 'UNKNOWN'}")
        
        now = datetime.now()

        # Trial info
        if subscription['trial_start_date']:
            trial_start = datetime.fromisoformat(subscription['trial_start_date'])
            print(f"\n🎁 Trial Started: {trial_start.strftime('%Y-%m-%d %H:%M:%S')}")

        if subscription['trial_end_date']:
            trial_end = datetime.fromisoformat(subscription['trial_end_date'])
            days_left = (trial_end - now).days
            print(f"⏰ Trial Ends: {trial_end.strftime('%Y-%m-%d %H:%M:%S')}")

            if days_left > 0:
                print(f"✅ Days Remaining: {days_left} days")
            else:
                print(f"❌ Trial Expired: {abs(days_left)} days ago")

        # Subscription info
        if subscription['subscription_start_date']:
            sub_start = datetime.fromisoformat(subscription['subscription_start_date'])
            print(f"\n💳 Subscription Started: {sub_start.strftime('%Y-%m-%d %H:%M:%S')}")

        if subscription['subscription_end_date']:
            sub_end = datetime.fromisoformat(subscription['subscription_end_date'])
            days_left = (sub_end - now).days
            print(f"⏰ Subscription Ends: {sub_end.strftime('%Y-%m-%d %H:%M:%S')}")

            if days_left > 0:
                print(f"✅ Days Remaining: {days_left} days")
            else:
                print(f"❌ Subscription Expired: {abs(days_left)} days ago")

        # Posting status
        status = subscription['subscription_status'] if subscription['subscription_status'] else 'unknown'
        posting_allowed = False

        if status == 'trial' and subscription['trial_end_date']:
            trial_end = datetime.fromisoformat(subscription['trial_end_date'])
            posting_allowed = trial_end > now
        elif status == 'active' and subscription['subscription_end_date']:
            sub_end = datetime.fromisoformat(subscription['subscription_end_date'])
            posting_allowed = sub_end > now
        elif status == 'grace_period' and subscription['grace_period_end']:
            grace_end = datetime.fromisoformat(subscription['grace_period_end'])
            posting_allowed = grace_end > now
        
        print(f"\n🚀 Posting Allowed: {'✅ YES' if posting_allowed else '❌ NO'}")

        print("\n" + "="*60)

        if not posting_allowed:
            print("\n💡 TO ENABLE POSTING:")
            print("   1. Use /renew command in the Telegram group to subscribe")
            print("   2. Or run: python check_subscription.py <group_id> extend <days>")
            print(f"      Example: python check_subscription.py {group_id} extend 30")

    finally:
        conn.close()

def extend_subscription(group_id: int, days: int):
    """Extend subscription for testing purposes."""
    # Connect to database
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM subscriptions WHERE group_id = ?", (group_id,))
        subscription = cursor.fetchone()

        if not subscription:
            print(f"\n❌ No subscription found for group {group_id}")
            print("💡 Use /setup command in the Telegram group first")
            return

        subscription_id = subscription['subscription_id']
        now = datetime.now()
        new_end_date = now + timedelta(days=days)

        # Update subscription
        cursor.execute("""
            UPDATE subscriptions
            SET subscription_status = ?,
                subscription_start_date = ?,
                subscription_end_date = ?,
                next_billing_date = ?,
                updated_at = ?
            WHERE subscription_id = ?
        """, (
            'active',
            now.isoformat(),
            new_end_date.isoformat(),
            (new_end_date - timedelta(days=7)).isoformat(),
            now.isoformat(),
            subscription_id
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
        print("✅ SUBSCRIPTION EXTENDED SUCCESSFULLY")
        print("="*60)
        print(f"\n📱 Group ID: {group_id}")
        print(f"📌 Status: ACTIVE")
        print(f"⏰ Valid Until: {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Days Added: {days} days")
        print("\n🚀 Posting is now ENABLED for this group!")
        print("\n" + "="*60)

    finally:
        conn.close()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("\n📖 USAGE:")
        print("   Check status:  python check_subscription.py <group_id>")
        print("   Extend trial:  python check_subscription.py <group_id> extend <days>")
        print("\n📝 EXAMPLES:")
        print("   python check_subscription.py -1002885984549")
        print("   python check_subscription.py -1002885984549 extend 30")
        return

    group_id = int(sys.argv[1])

    if len(sys.argv) >= 4 and sys.argv[2] == 'extend':
        days = int(sys.argv[3])
        extend_subscription(group_id, days)
    else:
        check_subscription_status(group_id)

if __name__ == "__main__":
    main()

