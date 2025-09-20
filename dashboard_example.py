#!/usr/bin/env python3
"""
DBBasic Dashboard Example - Shows all presentation layer components
This demonstrates how to build a complete dashboard using data structures
"""

from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer

# Initialize with extended components
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())

# Define a complete dashboard as data
dashboard = {
    'type': 'page',
    'title': 'DBBasic Dashboard',
    'components': [
        # Navigation
        {
            'type': 'navbar',
            'brand': 'DBBasic',
            'links': [
                {'text': 'Dashboard', 'url': '/'},
                {'text': 'Data', 'url': '/data'},
                {'text': 'Templates', 'url': '/templates'},
                {'text': 'Settings', 'url': '/settings'}
            ]
        },

        # Main container
        {
            'type': 'container',
            'children': [
                # Breadcrumb
                {
                    'type': 'breadcrumb',
                    'items': [
                        {'text': 'Home', 'url': '/'},
                        {'text': 'Dashboard', 'active': True}
                    ]
                },

                # Welcome alert
                {
                    'type': 'alert',
                    'message': 'Welcome to DBBasic Dashboard - Everything is data!',
                    'variant': 'primary',
                    'dismissible': True
                },

                # Stats cards row
                {
                    'type': 'grid',
                    'columns': 4,
                    'items': [
                        {
                            'type': 'card',
                            'title': 'Total Users',
                            'description': '1,234',
                            'category': 'Active'
                        },
                        {
                            'type': 'card',
                            'title': 'Templates',
                            'description': '42',
                            'category': 'Available'
                        },
                        {
                            'type': 'card',
                            'title': 'API Calls',
                            'description': '98,765',
                            'category': 'Today'
                        },
                        {
                            'type': 'card',
                            'title': 'Performance',
                            'description': '402M rows/sec',
                            'category': 'DuckDB'
                        }
                    ]
                },

                # Main content tabs
                {
                    'type': 'tabs',
                    'items': [
                        {
                            'id': 'overview-tab',
                            'label': 'Overview',
                            'active': True,
                            'content': {
                                'type': 'container',
                                'children': [
                                    # Progress indicators
                                    '<h5 class="mt-3">System Status</h5>',
                                    {
                                        'type': 'list_group',
                                        'items': [
                                            {
                                                'text': 'CPU Usage: 45%',
                                                'badge': 'Normal',
                                                'variant': 'success'
                                            },
                                            {
                                                'text': 'Memory: 2.3GB / 8GB',
                                                'badge': 'OK'
                                            },
                                            {
                                                'text': 'Disk: 120GB / 500GB',
                                                'badge': 'Good'
                                            }
                                        ]
                                    },

                                    '<h5 class="mt-4">Service Health</h5>',
                                    {
                                        'type': 'progress',
                                        'value': 85,
                                        'label': 'System Health: 85%',
                                        'variant': 'success',
                                        'striped': True
                                    }
                                ]
                            }
                        },
                        {
                            'id': 'data-tab',
                            'label': 'Data Tables',
                            'content': {
                                'type': 'table',
                                'striped': True,
                                'hover': True,
                                'headers': ['Service', 'Status', 'Port', 'Uptime', 'Actions'],
                                'rows': [
                                    [
                                        'CRUD Engine',
                                        {'type': 'badge', 'text': 'Running', 'variant': 'success'},
                                        '8005',
                                        '2 days',
                                        {'type': 'button', 'text': 'Restart', 'variant': 'sm'}
                                    ],
                                    [
                                        'AI Service',
                                        {'type': 'badge', 'text': 'Running', 'variant': 'success'},
                                        '8003',
                                        '2 days',
                                        {'type': 'button', 'text': 'Restart', 'variant': 'sm'}
                                    ],
                                    [
                                        'Monitor',
                                        {'type': 'badge', 'text': 'Running', 'variant': 'success'},
                                        '8004',
                                        '2 days',
                                        {'type': 'button', 'text': 'Restart', 'variant': 'sm'}
                                    ],
                                    [
                                        'Event Store',
                                        {'type': 'badge', 'text': 'Stopped', 'variant': 'danger'},
                                        '8006',
                                        'N/A',
                                        {'type': 'button', 'text': 'Start', 'variant': 'primary'}
                                    ]
                                ]
                            }
                        },
                        {
                            'id': 'templates-tab',
                            'label': 'Templates',
                            'content': {
                                'type': 'grid',
                                'columns': 3,
                                'items': [
                                    {
                                        'type': 'card',
                                        'title': 'Blog Platform',
                                        'category': 'CMS',
                                        'description': 'Full-featured blog with posts, categories, and SEO',
                                        'actions': ['deploy', 'preview']
                                    },
                                    {
                                        'type': 'card',
                                        'title': 'E-Commerce',
                                        'category': 'Shop',
                                        'description': 'Complete online store with products and orders',
                                        'actions': ['deploy', 'preview']
                                    },
                                    {
                                        'type': 'card',
                                        'title': 'CRM System',
                                        'category': 'Business',
                                        'description': 'Customer relationship management',
                                        'actions': ['deploy', 'preview']
                                    }
                                ]
                            }
                        },
                        {
                            'id': 'config-tab',
                            'label': 'Configuration',
                            'content': {
                                'type': 'form',
                                'fields': [
                                    {
                                        'type': 'input',
                                        'name': 'app_name',
                                        'label': 'Application Name',
                                        'value': 'My DBBasic App'
                                    },
                                    {
                                        'type': 'select',
                                        'name': 'theme',
                                        'label': 'UI Framework',
                                        'options': [
                                            {'value': 'bootstrap', 'text': 'Bootstrap 5.3', 'selected': True},
                                            {'value': 'tailwind', 'text': 'Tailwind CSS'},
                                            {'value': 'material', 'text': 'Material UI (Coming Soon)'}
                                        ]
                                    },
                                    {
                                        'type': 'select',
                                        'name': 'database',
                                        'label': 'Database',
                                        'options': [
                                            {'value': 'duckdb', 'text': 'DuckDB (402M rows/sec)', 'selected': True},
                                            {'value': 'sqlite', 'text': 'SQLite'},
                                            {'value': 'postgres', 'text': 'PostgreSQL'}
                                        ]
                                    },
                                    {
                                        'type': 'checkbox',
                                        'name': 'websockets',
                                        'label': 'Enable WebSocket real-time updates',
                                        'checked': True
                                    },
                                    {
                                        'type': 'checkbox',
                                        'name': 'ai_hooks',
                                        'label': 'Enable AI-powered business logic hooks',
                                        'checked': True
                                    },
                                    {
                                        'type': 'textarea',
                                        'name': 'notes',
                                        'label': 'Configuration Notes',
                                        'rows': 3,
                                        'placeholder': 'Any additional configuration notes...'
                                    }
                                ],
                                'buttons': [
                                    {'type': 'submit', 'text': 'Save Configuration', 'variant': 'primary'},
                                    {'type': 'reset', 'text': 'Reset', 'variant': 'secondary'}
                                ]
                            }
                        }
                    ]
                },

                # Activity feed
                '<h4 class="mt-5">Recent Activity</h4>',
                {
                    'type': 'accordion',
                    'id': 'activity-accordion',
                    'items': [
                        {
                            'header': 'Template Deployed - Blog Platform',
                            'body': 'User deployed the Blog Platform template at 10:45 AM',
                            'expanded': True
                        },
                        {
                            'header': 'Configuration Updated',
                            'body': 'Database settings were updated to use DuckDB'
                        },
                        {
                            'header': 'AI Service Generated',
                            'body': 'New shipping calculation service was generated'
                        }
                    ]
                },

                # Pagination
                '<div class="mt-4 d-flex justify-content-center">',
                {
                    'type': 'pagination',
                    'current': 1,
                    'total': 5
                },
                '</div>'
            ]
        }
    ]
}

# Generate the dashboard
html = PresentationLayer.render(dashboard, 'bootstrap')

# Save to file
with open('dashboard.html', 'w') as f:
    f.write(html)

print("✅ Generated dashboard.html - Complete DBBasic Dashboard")
print("\nThis dashboard demonstrates:")
print("- Navigation (navbar, breadcrumb)")
print("- Content (cards, alerts, badges)")
print("- Forms (all input types)")
print("- Tables (with embedded components)")
print("- Tabs, Accordion, Progress bars")
print("- Grid layouts and responsive design")
print("\nEverything defined as pure data structures!")