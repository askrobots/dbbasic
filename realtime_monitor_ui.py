#!/usr/bin/env python3
"""
Realtime Monitor UI Module
Provides UI data structures for the service
"""

from dbbasic_unified_ui import get_master_layout

def get_monitor_dashboard():
    """Get dashboard UI for monitor"""
    return get_master_layout(
        title='Monitor',
        service_name='monitor',
        content=[
            {
                'type': 'hero',
                'title': 'Monitor',
                'subtitle': 'Service dashboard'
            },
            {
                'type': 'div',
                'id': 'content',
                'children': []
            }
        ]
    )

def get_monitor_ui():
    """Get default UI for monitor"""
    return get_monitor_dashboard()
