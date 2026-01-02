"""
Contact and Group Management for WhatsApp MCP Server
Provides tools for accessing contact scanner data
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import os.path
import json

MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')

def get_all_contacts(
    include_metrics: bool = True,
    include_insights: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all contacts with optional metrics and insights."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.*,
                cm.last_message_date,
                cm.total_messages,
                ci.connection_strength,
                ci.relationship_status,
                ci.days_since_last_contact
            FROM contacts c
            LEFT JOIN conversation_metrics cm ON c.jid = cm.chat_jid
            LEFT JOIN contact_insights ci ON c.jid = ci.contact_jid
            ORDER BY cm.last_message_date DESC NULLS LAST
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (limit, offset))
        contacts = cursor.fetchall()
        
        result = []
        for contact in contacts:
            contact_dict = dict(contact)
            # Convert datetime strings to ISO format
            if contact_dict.get('first_seen'):
                contact_dict['first_seen'] = contact_dict['first_seen']
            if contact_dict.get('last_updated'):
                contact_dict['last_updated'] = contact_dict['last_updated']
            if contact_dict.get('last_message_date'):
                contact_dict['last_message_date'] = contact_dict['last_message_date']
            
            result.append(contact_dict)
        
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_contact(jid: str) -> Optional[Dict[str, Any]]:
    """Get single contact by JID."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.*,
                cm.last_message_date,
                cm.total_messages,
                cm.messages_sent,
                cm.messages_received,
                ci.connection_strength,
                ci.relationship_status,
                ci.days_since_last_contact,
                ci.mutual_group_count
            FROM contacts c
            LEFT JOIN conversation_metrics cm ON c.jid = cm.chat_jid
            LEFT JOIN contact_insights ci ON c.jid = ci.contact_jid
            WHERE c.jid = ?
        """
        
        cursor.execute(query, (jid,))
        contact = cursor.fetchone()
        
        if contact:
            return dict(contact)
        return None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_all_groups(
    include_members: bool = False,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all groups with optional member lists."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                g.*,
                COUNT(DISTINCT gm.member_jid) as current_member_count,
                cm.total_messages,
                cm.last_message_date
            FROM groups g
            LEFT JOIN group_members gm ON g.jid = gm.group_jid AND gm.left_at IS NULL
            LEFT JOIN conversation_metrics cm ON g.jid = cm.chat_jid
            GROUP BY g.jid
            ORDER BY cm.last_message_date DESC NULLS LAST
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (limit, offset))
        groups = cursor.fetchall()
        
        result = []
        for group in groups:
            group_dict = dict(group)
            
            if include_members:
                # Get member list
                cursor.execute("""
                    SELECT 
                        gm.member_jid,
                        c.full_name,
                        c.push_name,
                        gm.is_admin,
                        gm.is_super_admin,
                        gm.joined_at
                    FROM group_members gm
                    LEFT JOIN contacts c ON gm.member_jid = c.jid
                    WHERE gm.group_jid = ? AND gm.left_at IS NULL
                    ORDER BY gm.is_super_admin DESC, gm.is_admin DESC, gm.joined_at ASC
                """, (group_dict['jid'],))
                
                members = cursor.fetchall()
                group_dict['members'] = [dict(m) for m in members]
            
            result.append(group_dict)
        
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_group_info(jid: str, include_members: bool = True) -> Optional[Dict[str, Any]]:
    """Get group information by JID."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                g.*,
                COUNT(DISTINCT gm.member_jid) as current_member_count,
                cm.total_messages,
                cm.last_message_date
            FROM groups g
            LEFT JOIN group_members gm ON g.jid = gm.group_jid AND gm.left_at IS NULL
            LEFT JOIN conversation_metrics cm ON g.jid = cm.chat_jid
            WHERE g.jid = ?
            GROUP BY g.jid
        """
        
        cursor.execute(query, (jid,))
        group = cursor.fetchone()
        
        if not group:
            return None
        
        group_dict = dict(group)
        
        if include_members:
            # Get member list
            cursor.execute("""
                SELECT 
                    gm.member_jid,
                    c.full_name,
                    c.push_name,
                    gm.is_admin,
                    gm.is_super_admin,
                    gm.joined_at,
                    gm.left_at,
                    gm.added_by_jid
                FROM group_members gm
                LEFT JOIN contacts c ON gm.member_jid = c.jid
                WHERE gm.group_jid = ?
                ORDER BY gm.left_at IS NULL DESC, gm.is_super_admin DESC, gm.is_admin DESC, gm.joined_at ASC
            """, (jid,))
            
            members = cursor.fetchall()
            group_dict['members'] = [dict(m) for m in members]
        
        return group_dict
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_conversation_topics(
    chat_jid: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    min_mentions: int = 2
) -> List[Dict[str, Any]]:
    """Get conversation topics, optionally filtered by chat or keyword."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ct.*,
                c.name as chat_name
            FROM conversation_topics ct
            JOIN chats c ON ct.chat_jid = c.jid
            WHERE ct.mention_count >= ?
        """
        
        params = [min_mentions]
        
        if chat_jid:
            query += " AND ct.chat_jid = ?"
            params.append(chat_jid)
        
        if keyword:
            query += " AND ct.keyword LIKE ?"
            params.append(f"%{keyword}%")
        
        query += " ORDER BY ct.importance_score DESC, ct.mention_count DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        topics = cursor.fetchall()
        
        return [dict(t) for t in topics]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_active_contacts(days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """Get contacts with recent activity."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.*,
                cm.last_message_date,
                cm.total_messages,
                ci.connection_strength
            FROM contacts c
            JOIN conversation_metrics cm ON c.jid = cm.chat_jid
            LEFT JOIN contact_insights ci ON c.jid = ci.contact_jid
            WHERE cm.last_message_date >= datetime('now', ? || ' days')
            ORDER BY cm.last_message_date DESC
            LIMIT ?
        """
        
        cursor.execute(query, (f'-{days}', limit))
        contacts = cursor.fetchall()
        
        return [dict(c) for c in contacts]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_dormant_contacts(days: int = 90, limit: int = 100) -> List[Dict[str, Any]]:
    """Get contacts without recent activity."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.*,
                cm.last_message_date,
                julianday('now') - julianday(cm.last_message_date) as days_since_last_message,
                ci.connection_strength
            FROM contacts c
            JOIN conversation_metrics cm ON c.jid = cm.chat_jid
            LEFT JOIN contact_insights ci ON c.jid = ci.contact_jid
            WHERE cm.last_message_date < datetime('now', ? || ' days')
            ORDER BY cm.last_message_date ASC
            LIMIT ?
        """
        
        cursor.execute(query, (f'-{days}', limit))
        contacts = cursor.fetchall()
        
        return [dict(c) for c in contacts]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_interesting_topics() -> List[Dict[str, Any]]:
    """Get user-defined interesting topics to track."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM interesting_topics
            ORDER BY importance DESC, keyword ASC
        """)
        
        topics = cursor.fetchall()
        return [dict(t) for t in topics]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def add_interesting_topic(
    keyword: str,
    category: Optional[str] = None,
    importance: float = 1.0,
    notify_on_mention: bool = False,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new interesting topic to track."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interesting_topics (keyword, category, importance, notify_on_mention, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (keyword, category, importance, notify_on_mention, notes))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Added topic: {keyword}",
            "id": cursor.lastrowid
        }
        
    except sqlite3.IntegrityError:
        return {
            "success": False,
            "message": f"Topic '{keyword}' already exists"
        }
    except sqlite3.Error as e:
        return {
            "success": False,
            "message": f"Database error: {e}"
        }
    finally:
        if 'conn' in locals():
            conn.close()


def get_topic_alerts(acknowledged: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
    """Get topic alerts (mentions of interesting topics)."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ta.*,
                it.category,
                it.importance,
                c.name as chat_name
            FROM topic_alerts ta
            JOIN interesting_topics it ON ta.topic_keyword = it.keyword
            JOIN chats c ON ta.chat_jid = c.jid
            WHERE ta.acknowledged = ?
            ORDER BY ta.detected_at DESC
            LIMIT ?
        """
        
        cursor.execute(query, (1 if acknowledged else 0, limit))
        alerts = cursor.fetchall()
        
        return [dict(a) for a in alerts]
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

