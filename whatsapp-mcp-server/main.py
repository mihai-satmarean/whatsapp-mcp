from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from whatsapp import (
    search_contacts as whatsapp_search_contacts,
    list_messages as whatsapp_list_messages,
    list_chats as whatsapp_list_chats,
    get_chat as whatsapp_get_chat,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_contact_chats as whatsapp_get_contact_chats,
    get_last_interaction as whatsapp_get_last_interaction,
    get_message_context as whatsapp_get_message_context,
    send_message as whatsapp_send_message,
    send_file as whatsapp_send_file,
    send_audio_message as whatsapp_audio_voice_message,
    download_media as whatsapp_download_media
)
from contacts import (
    get_all_contacts,
    get_contact,
    get_all_groups,
    get_group_info,
    get_conversation_topics,
    get_active_contacts,
    get_dormant_contacts,
    get_interesting_topics,
    add_interesting_topic,
    get_topic_alerts
)

# Initialize FastMCP server
mcp = FastMCP("whatsapp")

@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    
    Args:
        query: Search term to match against contact names or phone numbers
    """
    contacts = whatsapp_search_contacts(query)
    return contacts

@mcp.tool()
def list_messages(
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> List[Dict[str, Any]]:
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
    """
    messages = whatsapp_list_messages(
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after
    )
    return messages

@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria.
    
    Args:
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")
    """
    chats = whatsapp_list_chats(
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by
    )
    return chats

@mcp.tool()
def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID.
    
    Args:
        chat_jid: The JID of the chat to retrieve
        include_last_message: Whether to include the last message (default True)
    """
    chat = whatsapp_get_chat(chat_jid, include_last_message)
    return chat

@mcp.tool()
def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number.
    
    Args:
        sender_phone_number: The phone number to search for
    """
    chat = whatsapp_get_direct_chat_by_contact(sender_phone_number)
    return chat

@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact.
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    chats = whatsapp_get_contact_chats(jid, limit, page)
    return chats

@mcp.tool()
def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact.
    
    Args:
        jid: The JID of the contact to search for
    """
    message = whatsapp_get_last_interaction(jid)
    return message

@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message.
    
    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default 5)
        after: Number of messages to include after the target message (default 5)
    """
    context = whatsapp_get_message_context(message_id, before, after)
    return context

@mcp.tool()
def send_message(
    recipient: str,
    message: str
) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group. For group chats use the JID.

    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    # Validate input
    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided"
        }
    
    # Call the whatsapp_send_message function with the unified recipient parameter
    success, status_message = whatsapp_send_message(recipient, message)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file such as a picture, raw audio, video or document via WhatsApp to the specified recipient. For group messages use the JID.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the media file to send (image, video, document)
    
    Returns:
        A dictionary containing success status and a status message
    """
    
    # Call the whatsapp_send_file function
    success, status_message = whatsapp_send_file(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send any audio file as a WhatsApp audio message to the specified recipient. For group messages use the JID. If it errors due to ffmpeg not being installed, use send_file instead.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the audio file to send (will be converted to Opus .ogg if it's not a .ogg file)
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp_audio_voice_message(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    file_path = whatsapp_download_media(message_id, chat_jid)
    
    if file_path:
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path
        }
    else:
        return {
            "success": False,
            "message": "Failed to download media"
        }

# ============================================================
# CONTACT SCANNER TOOLS
# ============================================================

@mcp.tool()
def list_all_contacts(
    include_metrics: bool = True,
    include_insights: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all contacts from the contact scanner database with optional metrics and insights.
    
    Args:
        include_metrics: Include conversation metrics (default True)
        include_insights: Include relationship insights (default True)
        limit: Maximum number of contacts to return (default 100)
        offset: Offset for pagination (default 0)
    
    Returns:
        List of contacts with their details, metrics, and insights
    """
    return get_all_contacts(include_metrics, include_insights, limit, offset)

@mcp.tool()
def get_contact_details(jid: str) -> Dict[str, Any]:
    """Get detailed information about a specific contact including metrics and insights.
    
    Args:
        jid: The JID of the contact
    
    Returns:
        Contact details with metrics and insights, or None if not found
    """
    contact = get_contact(jid)
    return contact if contact else {"error": "Contact not found"}

@mcp.tool()
def list_all_groups(
    include_members: bool = False,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all WhatsApp groups from the contact scanner database.
    
    Args:
        include_members: Include member lists for each group (default False)
        limit: Maximum number of groups to return (default 100)
        offset: Offset for pagination (default 0)
    
    Returns:
        List of groups with their details and optionally member lists
    """
    return get_all_groups(include_members, limit, offset)

@mcp.tool()
def get_group_details(jid: str, include_members: bool = True) -> Dict[str, Any]:
    """Get detailed information about a specific WhatsApp group including members.
    
    Args:
        jid: The JID of the group
        include_members: Include member list (default True)
    
    Returns:
        Group details with member list, or None if not found
    """
    group = get_group_info(jid, include_members)
    return group if group else {"error": "Group not found"}

@mcp.tool()
def list_conversation_topics(
    chat_jid: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    min_mentions: int = 2
) -> List[Dict[str, Any]]:
    """Get conversation topics tracked across chats.
    
    Args:
        chat_jid: Optional - filter by specific chat JID
        keyword: Optional - filter by keyword pattern
        limit: Maximum number of topics to return (default 50)
        min_mentions: Minimum mention count (default 2)
    
    Returns:
        List of topics with mention counts, importance scores, and last mentioned dates
    """
    return get_conversation_topics(chat_jid, keyword, limit, min_mentions)

@mcp.tool()
def list_active_contacts(days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """Get contacts with recent activity.
    
    Args:
        days: Number of days to look back (default 30)
        limit: Maximum number of contacts to return (default 100)
    
    Returns:
        List of active contacts ordered by last message date
    """
    return get_active_contacts(days, limit)

@mcp.tool()
def list_dormant_contacts(days: int = 90, limit: int = 100) -> List[Dict[str, Any]]:
    """Get contacts without recent activity (for reconnection opportunities).
    
    Args:
        days: Number of days threshold (default 90)
        limit: Maximum number of contacts to return (default 100)
    
    Returns:
        List of dormant contacts ordered by days since last contact
    """
    return get_dormant_contacts(days, limit)

@mcp.tool()
def list_interesting_topics() -> List[Dict[str, Any]]:
    """Get user-defined interesting topics being tracked.
    
    Returns:
        List of interesting topics with their categories and importance scores
    """
    return get_interesting_topics()

@mcp.tool()
def add_topic_to_track(
    keyword: str,
    category: Optional[str] = None,
    importance: float = 1.0,
    notify_on_mention: bool = False,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new interesting topic to track across conversations.
    
    Args:
        keyword: The keyword or phrase to track
        category: Optional category (e.g., 'business', 'personal', 'tech')
        importance: Importance weight (0.0 to 10.0, default 1.0)
        notify_on_mention: Whether to create alerts when mentioned (default False)
        notes: Optional notes about this topic
    
    Returns:
        Success status and message
    """
    return add_interesting_topic(keyword, category, importance, notify_on_mention, notes)

@mcp.tool()
def list_topic_alerts(acknowledged: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
    """Get alerts for mentions of interesting topics.
    
    Args:
        acknowledged: Whether to show acknowledged alerts (default False - shows new only)
        limit: Maximum number of alerts to return (default 100)
    
    Returns:
        List of topic alerts with context and importance
    """
    return get_topic_alerts(acknowledged, limit)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')