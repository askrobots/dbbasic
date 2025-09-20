#!/usr/bin/env python3
"""
Dbbasic Crud Engine UI Module
Provides UI data structures for the service
"""

from dbbasic_unified_ui import get_master_layout

def get_data_dashboard():
    """Get dashboard UI for data"""
    return get_master_layout(
        title='Data',
        service_name='data',
        content=[
            {
                'type': 'hero',
                'title': 'Data',
                'subtitle': 'Service dashboard'
            },
            {
                'type': 'div',
                'id': 'content',
                'children': []
            }
        ]
    )

def get_data_ui():
    """Get default UI for data"""
    return get_data_dashboard()
