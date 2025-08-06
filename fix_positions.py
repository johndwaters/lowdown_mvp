#!/usr/bin/env python3
"""
Position Initialization Script for The Lowdown
Fixes missing position values for existing articles and snapshots
"""

import sqlite3
import os

def fix_positions():
    """Initialize position values for all existing articles and snapshots"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'lowdown.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing article positions...")
        
        # Get all articles without positions, ordered by creation date
        cursor.execute("""
            SELECT id FROM articles 
            WHERE position IS NULL 
            ORDER BY created_at ASC
        """)
        articles_without_positions = cursor.fetchall()
        
        # Get the highest existing position
        cursor.execute("SELECT MAX(position) FROM articles WHERE position IS NOT NULL")
        max_position = cursor.fetchone()[0] or 0
        
        # Assign positions to articles without them
        for i, (article_id,) in enumerate(articles_without_positions, start=max_position + 1):
            cursor.execute("""
                UPDATE articles 
                SET position = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (i, article_id))
            print(f"   📄 Article {article_id} → position {i}")
        
        print("🔧 Fixing snapshot positions...")
        
        # Get all snapshots without positions, ordered by creation date
        cursor.execute("""
            SELECT id FROM snapshots 
            WHERE position IS NULL 
            ORDER BY created_at ASC
        """)
        snapshots_without_positions = cursor.fetchall()
        
        # Get the highest existing position
        cursor.execute("SELECT MAX(position) FROM snapshots WHERE position IS NOT NULL")
        max_position = cursor.fetchone()[0] or 0
        
        # Assign positions to snapshots without them
        for i, (snapshot_id,) in enumerate(snapshots_without_positions, start=max_position + 1):
            cursor.execute("""
                UPDATE snapshots 
                SET position = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (i, snapshot_id))
            print(f"   📷 Snapshot {snapshot_id} → position {i}")
        
        # Commit changes
        conn.commit()
        
        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM articles WHERE position IS NULL")
        articles_without_pos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM snapshots WHERE position IS NULL")
        snapshots_without_pos = cursor.fetchone()[0]
        
        print(f"\n✅ Position fix complete!")
        print(f"   📄 Articles without positions: {articles_without_pos}")
        print(f"   📷 Snapshots without positions: {snapshots_without_pos}")
        
        if articles_without_pos == 0 and snapshots_without_pos == 0:
            print("🎯 All items now have valid positions!")
            return True
        else:
            print("⚠️  Some items still missing positions")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing positions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting position initialization...")
    success = fix_positions()
    if success:
        print("✅ Position fix completed successfully!")
    else:
        print("❌ Position fix failed!")
