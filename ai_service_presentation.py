#!/usr/bin/env python3
"""
AI Service Builder UI using Presentation Layer
Converts all HTML generation to data structures
"""

from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer

# Initialize presentation layer
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())

def get_ai_service_dashboard():
    """Generate AI Service Builder dashboard as data structure"""
    return {
        'type': 'page',
        'title': 'DBBasic AI Service Platform',
        'components': [
            # Navigation
            {
                'type': 'navbar',
                'brand': 'DBBasic',
                'variant': 'dark',
                'links': [
                    {'text': 'Monitor', 'url': 'http://localhost:8004'},
                    {'text': 'Data', 'url': 'http://localhost:8005'},
                    {'text': 'AI Services', 'url': 'http://localhost:8003'},
                    {'text': 'Event Store', 'url': 'http://localhost:8006'},
                    {'text': 'Templates', 'url': 'http://localhost:8005/templates'}
                ]
            },

            # Header with status
            {
                'type': 'container',
                'fluid': True,
                'children': [
                    {
                        'type': 'hero',
                        'title': '🤖 AI Service Platform',
                        'subtitle': 'Config → Code → Tests • 402M rows/sec • Post-Code Era'
                    },

                    # Status badges
                    {
                        'type': 'container',
                        'children': [
                            '<div class="text-center mb-4">',
                            {'type': 'badge', 'text': '🚀 402M rows/sec', 'variant': 'success', 'pill': True},
                            ' ',
                            {'type': 'badge', 'text': '⚡ Post-Code Era', 'variant': 'info', 'pill': True},
                            ' ',
                            {'type': 'badge', 'text': '🔗 All Services Connected', 'variant': 'primary', 'pill': True},
                            '</div>'
                        ]
                    }
                ]
            },

            # Services grid
            {
                'type': 'container',
                'children': [
                    {
                        'type': 'grid',
                        'columns': 3,
                        'items': [
                            {
                                'type': 'card',
                                'title': '🛠️ Service Builder',
                                'description': 'Create AI services from natural language descriptions. Generate code, config, and tests automatically.',
                                'actions': [
                                    {'type': 'button', 'text': 'Build Services', 'variant': 'primary', 'onclick': "location.href='/fresh'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '🧪 Test Runner',
                                'description': 'Run comprehensive tests for all generated services. Validate functionality and catch regressions.',
                                'actions': [
                                    {'type': 'button', 'text': 'Run Tests', 'variant': 'success', 'onclick': "location.href='/tests'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '📊 System Logs',
                                'description': 'Monitor service executions, rule applications, and system performance in real-time.',
                                'actions': [
                                    {'type': 'button', 'text': 'View Logs', 'variant': 'warning', 'onclick': "location.href='/logs'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '⚙️ Config Examples',
                                'description': 'Explore config-driven services and see how business logic becomes executable YAML.',
                                'actions': [
                                    {'type': 'button', 'text': 'Browse Configs', 'variant': 'info', 'onclick': "location.href='/config'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '📋 Service Status',
                                'description': 'View all active services, their endpoints, and real-time performance metrics.',
                                'actions': [
                                    {'type': 'button', 'text': 'View Services', 'variant': 'secondary', 'onclick': "location.href='/api/services'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '🔍 Code Viewer',
                                'description': 'Browse generated service code with syntax highlighting and direct endpoint access.',
                                'actions': [
                                    {'type': 'button', 'text': 'View Code', 'variant': 'dark', 'onclick': "location.href='/code'"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '📡 Real-time Monitor',
                                'category': 'External',
                                'description': 'Watch live service activity with WebSocket updates. See actual service execution in real-time.',
                                'actions': [
                                    {'type': 'button', 'text': 'Open Monitor →', 'variant': 'primary', 'onclick': "window.open('http://localhost:8004')"}
                                ]
                            },
                            {
                                'type': 'card',
                                'title': '✅ Test Runner Web',
                                'category': 'External',
                                'description': 'Run tests from your browser and see red/green results with live output streaming.',
                                'actions': [
                                    {'type': 'button', 'text': 'Open Test Runner →', 'variant': 'success', 'onclick': "window.open('http://localhost:8006')"}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

def get_test_runner_ui():
    """Generate test runner interface as data structure"""
    return {
        'type': 'page',
        'title': 'DBBasic Test Runner',
        'components': [
            {
                'type': 'navbar',
                'brand': 'DBBasic Test Runner',
                'links': [
                    {'text': '← Back to Dashboard', 'url': '/'}
                ]
            },
            {
                'type': 'container',
                'children': [
                    {
                        'type': 'alert',
                        'message': 'Test Runner - Run all AI service tests',
                        'variant': 'info'
                    },
                    '<div class="text-center my-4">',
                    {
                        'type': 'button',
                        'text': '🧪 Run All Tests',
                        'variant': 'primary',
                        'onclick': 'runTests()'
                    },
                    '</div>',
                    '<div id="status" class="text-center mb-3">Ready to run tests</div>',
                    '<div id="results"></div>'
                ]
            }
        ]
    }

def get_logs_viewer_ui():
    """Generate logs viewer interface as data structure"""
    return {
        'type': 'page',
        'title': 'DBBasic System Logs',
        'components': [
            {
                'type': 'navbar',
                'brand': 'System Logs & Monitoring',
                'links': [
                    {'text': '← Back', 'url': '/'}
                ]
            },
            {
                'type': 'container',
                'children': [
                    # Stats cards
                    {
                        'type': 'grid',
                        'columns': 3,
                        'items': [
                            {
                                'type': 'card',
                                'title': 'Active Services',
                                'description': '<span id="activeServices">-</span>'
                            },
                            {
                                'type': 'card',
                                'title': 'Log Entries',
                                'description': '<span id="totalLogs">-</span>'
                            },
                            {
                                'type': 'card',
                                'title': 'Errors',
                                'description': '<span id="errorCount">-</span>'
                            }
                        ]
                    },

                    # Controls
                    '<div class="my-3">',
                    {
                        'type': 'button',
                        'text': '🔄 Refresh',
                        'variant': 'primary',
                        'onclick': 'loadLogs()'
                    },
                    ' ',
                    '<select id="levelFilter" class="form-select d-inline-block w-auto ms-2" onchange="loadLogs()">',
                    '<option value="all">All Levels</option>',
                    '<option value="ERROR">Errors Only</option>',
                    '<option value="WARNING">Warnings & Errors</option>',
                    '<option value="INFO">Info & Above</option>',
                    '</select>',
                    '</div>',

                    # Logs container
                    '<div id="logs" class="border rounded p-3 bg-light" style="min-height: 400px; font-family: monospace;">',
                    'Loading logs...',
                    '</div>'
                ]
            }
        ]
    }

def get_service_builder_form():
    """Generate service builder form as data structure"""
    return {
        'type': 'page',
        'title': 'AI Service Builder',
        'components': [
            {
                'type': 'navbar',
                'brand': 'AI Service Builder',
                'links': [
                    {'text': '← Back', 'url': '/'}
                ]
            },
            {
                'type': 'container',
                'children': [
                    {
                        'type': 'alert',
                        'message': 'Describe your service in natural language and AI will generate the code',
                        'variant': 'info'
                    },
                    {
                        'type': 'form',
                        'action': '/api/services/create',
                        'method': 'POST',
                        'fields': [
                            {
                                'type': 'input',
                                'name': 'service_name',
                                'label': 'Service Name',
                                'placeholder': 'e.g., calculate_shipping',
                                'required': True
                            },
                            {
                                'type': 'textarea',
                                'name': 'description',
                                'label': 'Service Description',
                                'placeholder': 'Describe what this service should do in natural language...',
                                'rows': 6,
                                'required': True,
                                'help': 'Example: Calculate shipping cost based on weight, distance, and shipping method. For express shipping add 50% surcharge.'
                            },
                            {
                                'type': 'input',
                                'name': 'inputs',
                                'label': 'Input Parameters',
                                'placeholder': 'e.g., weight, distance, method',
                                'help': 'Comma-separated list of input parameters'
                            },
                            {
                                'type': 'input',
                                'name': 'outputs',
                                'label': 'Output Fields',
                                'placeholder': 'e.g., cost, estimated_days',
                                'help': 'Comma-separated list of output fields'
                            },
                            {
                                'type': 'checkbox',
                                'name': 'generate_tests',
                                'label': 'Generate unit tests',
                                'checked': True
                            },
                            {
                                'type': 'checkbox',
                                'name': 'add_to_hooks',
                                'label': 'Register as model hook',
                                'checked': False
                            }
                        ],
                        'buttons': [
                            {'type': 'submit', 'text': '🚀 Generate Service', 'variant': 'primary'},
                            {'type': 'reset', 'text': 'Clear', 'variant': 'secondary'}
                        ]
                    }
                ]
            }
        ]
    }

# Example usage
if __name__ == "__main__":
    # Generate all AI Service UIs
    dashboard_html = PresentationLayer.render(get_ai_service_dashboard(), 'bootstrap')
    test_runner_html = PresentationLayer.render(get_test_runner_ui(), 'bootstrap')
    logs_viewer_html = PresentationLayer.render(get_logs_viewer_ui(), 'bootstrap')
    builder_form_html = PresentationLayer.render(get_service_builder_form(), 'bootstrap')

    # Save examples
    with open('ai_dashboard_new.html', 'w') as f:
        f.write(dashboard_html)

    print("✅ Generated AI Service UIs using presentation layer")
    print("\nToken savings estimate:")
    print("- Old HTML: ~2000 lines → ~50,000 tokens")
    print("- New data structures: ~200 lines → ~5,000 tokens")
    print("- Reduction: 90% fewer tokens!")
    print("\nBenefits:")
    print("- 10x faster AI generation")
    print("- Cleaner, maintainable code")
    print("- Framework agnostic")
    print("- Easy to modify and test")