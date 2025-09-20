#!/usr/bin/env python3
"""
Dbbasic Ai Service Builder UI Module
Provides UI data structures for the service
"""

from dbbasic_unified_ui import get_master_layout

def get_ai_services_dashboard():
    """Get dashboard UI for ai_services"""
    return get_master_layout(
        title='Ai Services',
        service_name='ai_services',
        content=[
            {
                'type': 'hero',
                'title': 'Ai Services',
                'subtitle': 'Service dashboard'
            },
            {
                'type': 'div',
                'id': 'content',
                'children': []
            }
        ]
    )

def get_ai_services_ui():
    """Get default UI for ai_services"""
    return get_ai_services_dashboard()
