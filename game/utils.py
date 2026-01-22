"""
Utility functions for WebSocket broadcasting.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_admin_question(room_code, question_data):
    """Broadcast admin-injected question to all clients in the room."""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'game_{room_code}',
            {
                'type': 'admin_question_injected',
                'room_code': room_code,
                'question': question_data
            }
        )


def broadcast_standalone_question(session_id, question_data):
    """Broadcast admin-injected question to standalone user."""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'standalone_{session_id}',
            {
                'type': 'admin_question_injected',
                'session_id': session_id,
                'question': question_data
            }
        )
