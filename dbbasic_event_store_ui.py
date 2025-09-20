#!/usr/bin/env python3
"""
Dbbasic Event Store UI Module
Provides UI data structures for the service
"""

from dbbasic_unified_ui import get_master_layout

def get_event_store_dashboard():
    """Get dashboard UI for event_store"""
    return get_master_layout(
        title='Event Store',
        service_name='event_store',
        content=[
            {
                'type': 'hero',
                'title': 'Event Store',
                'subtitle': 'Service dashboard'
            },
            {
                'type': 'div',
                'id': 'content',
                'children': []
            }
        ]
    )

def get_event_store_ui():
    """Get default UI for event_store"""
    return get_event_store_dashboard()
