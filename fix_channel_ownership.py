"""
Fix channel ownership for existing channels.
This script updates creator_user_id for channels that were registered before the column was added.
"""

import sqlite3
import sys

def fix_channel_ownership(channel_id: int, user_id: int):
    """Update creator_user_id for a specific channel."""
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # Check if channel exists
        cursor.execute("SELECT group_id, group_name FROM groups WHERE group_id = ?", (channel_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Channel {channel_id} not found in database")
            conn.close()
            return False
        
        channel_name = result[1]
        print(f"📺 Found channel: {channel_name} (ID: {channel_id})")
        
        # Update creator_user_id
        cursor.execute("""
            UPDATE groups SET creator_user_id = ? WHERE group_id = ?
        """, (user_id, channel_id))
        
        conn.commit()
        
        # Verify update
        cursor.execute("SELECT creator_user_id FROM groups WHERE group_id = ?", (channel_id,))
        updated = cursor.fetchone()
        
        if updated and updated[0] == user_id:
            print(f"✅ Successfully set creator_user_id = {user_id} for channel {channel_id}")
            conn.close()
            return True
        else:
            print(f"❌ Failed to update creator_user_id")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_channels_without_owner():
    """List all channels that don't have a creator_user_id set."""
    try:
        conn = sqlite3.connect('bot_database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT group_id, group_name, created_at 
            FROM groups 
            WHERE creator_user_id IS NULL
            ORDER BY created_at DESC
        """)
        
        channels = cursor.fetchall()
        conn.close()
        
        if not channels:
            print("✅ All channels have owners assigned!")
            return []
        
        print(f"\n📋 Found {len(channels)} channel(s) without owner:\n")
        for ch in channels:
            print(f"  • {ch['group_name']} (ID: {ch['group_id']}) - Created: {ch['created_at']}")
        
        return channels
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Channel Ownership Fix Tool")
    print("=" * 60)
    
    if len(sys.argv) == 3:
        # Fix specific channel
        try:
            channel_id = int(sys.argv[1])
            user_id = int(sys.argv[2])
            
            print(f"\n🔄 Updating channel {channel_id} with owner {user_id}...\n")
            success = fix_channel_ownership(channel_id, user_id)
            
            if success:
                print("\n✅ Done!")
            else:
                print("\n❌ Failed!")
                sys.exit(1)
                
        except ValueError:
            print("❌ Invalid arguments. Both channel_id and user_id must be numbers.")
            sys.exit(1)
    else:
        # List channels without owners
        print("\n📋 Listing channels without owners...\n")
        channels = list_channels_without_owner()
        
        if channels:
            print("\n" + "=" * 60)
            print("💡 To fix a channel, run:")
            print("   python fix_channel_ownership.py <channel_id> <user_id>")
            print("\nExample:")
            print("   python fix_channel_ownership.py -1003180920354 123456789")
            print("=" * 60)

