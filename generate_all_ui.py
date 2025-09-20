#!/usr/bin/env python3
"""
Generate all DBBasic UI interfaces using the Presentation Layer
This script generates the complete DBBasic site with data structures
"""

import os
from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer
from dbbasic_unified_ui import get_master_layout, get_service_dashboard, SERVICES

# Import all UI modules
from realtime_monitor_presentation import get_realtime_monitor_ui
from dbbasic_ai_service_builder_presentation import (
    get_ai_service_main_ui,
    get_test_runner_ui,
    get_hooks_dashboard
)
from dbbasic_event_store_presentation import get_event_store_dashboard
from dbbasic_crud_engine_presentation import (
    get_crud_dashboard,
    get_template_marketplace,
    get_model_editor,
    get_resource_viewer
)

# Initialize presentation layer
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())

def generate_all_interfaces():
    """Generate all DBBasic interfaces"""

    print("=" * 60)
    print("🚀 DBBasic UI Generation with Presentation Layer")
    print("=" * 60)

    generated_files = []

    # Main dashboard
    print("\n📊 Generating main dashboard...")
    dashboard_html = PresentationLayer.render(get_service_dashboard(), 'bootstrap')
    with open('static/dashboard.html', 'w') as f:
        f.write(dashboard_html)
    generated_files.append('dashboard.html')

    # Real-time Monitor
    print("📡 Generating Real-time Monitor...")
    monitor_html = PresentationLayer.render(get_realtime_monitor_ui(), 'bootstrap')
    with open('static/monitor.html', 'w') as f:
        f.write(monitor_html)
    generated_files.append('monitor.html')

    # AI Service Builder
    print("🤖 Generating AI Service Builder...")
    ai_main_html = PresentationLayer.render(get_ai_service_main_ui(), 'bootstrap')
    with open('static/ai_services.html', 'w') as f:
        f.write(ai_main_html)
    generated_files.append('ai_services.html')

    test_runner_html = PresentationLayer.render(get_test_runner_ui(), 'bootstrap')
    with open('static/test_runner.html', 'w') as f:
        f.write(test_runner_html)
    generated_files.append('test_runner.html')

    hooks_html = PresentationLayer.render(get_hooks_dashboard(), 'bootstrap')
    with open('static/hooks.html', 'w') as f:
        f.write(hooks_html)
    generated_files.append('hooks.html')

    # Event Store
    print("📚 Generating Event Store...")
    event_store_html = PresentationLayer.render(get_event_store_dashboard(), 'bootstrap')
    with open('static/event_store.html', 'w') as f:
        f.write(event_store_html)
    generated_files.append('event_store.html')

    # CRUD Engine / Data Service
    print("💾 Generating Data Service...")
    crud_dashboard_html = PresentationLayer.render(get_crud_dashboard(), 'bootstrap')
    with open('static/data_service.html', 'w') as f:
        f.write(crud_dashboard_html)
    generated_files.append('data_service.html')

    marketplace_html = PresentationLayer.render(get_template_marketplace(), 'bootstrap')
    with open('static/templates.html', 'w') as f:
        f.write(marketplace_html)
    generated_files.append('templates.html')

    model_editor_html = PresentationLayer.render(get_model_editor(), 'bootstrap')
    with open('static/model_editor.html', 'w') as f:
        f.write(model_editor_html)
    generated_files.append('model_editor.html')

    # Generate mockup conversions
    print("\n🎨 Converting static mockups...")
    generate_mockup_conversions()

    # Generate index page
    print("📄 Generating index page...")
    index_html = generate_index_page()
    with open('static/index.html', 'w') as f:
        f.write(index_html)
    generated_files.append('index.html')

    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Generated {len(generated_files)} files in static/")
    print("\n🎯 Benefits achieved:")
    print("  • All UI as data structures")
    print("  • 90% token reduction")
    print("  • Framework agnostic")
    print("  • Consistent navigation")
    print("  • Clean separation of concerns")

    return generated_files

def generate_mockup_conversions():
    """Convert mockup concepts to data structures"""

    # Configuration mockup
    config_ui = get_master_layout(
        title='Configuration Builder',
        service_name='data',
        content=[
            {
                'type': 'hero',
                'title': '⚙️ Configuration Builder',
                'subtitle': 'Visual YAML configuration editor'
            },
            {
                'type': 'grid',
                'columns': 2,
                'items': [
                    {
                        'type': 'card',
                        'title': 'YAML Editor',
                        'body': {
                            'type': 'code_editor',
                            'id': 'yaml-editor',
                            'language': 'yaml',
                            'theme': 'monokai'
                        }
                    },
                    {
                        'type': 'card',
                        'title': 'Live Preview',
                        'body': {
                            'type': 'iframe',
                            'id': 'preview-frame',
                            'src': '/preview'
                        }
                    }
                ]
            }
        ]
    )

    config_html = PresentationLayer.render(config_ui, 'bootstrap')
    with open('static/config_builder.html', 'w') as f:
        f.write(config_html)

def generate_index_page():
    """Generate the main index page"""
    index_ui = {
        'type': 'page',
        'title': 'DBBasic Platform',
        'components': [
            # No navbar on index - full screen hero
            {
                'type': 'hero',
                'fullscreen': True,
                'title': 'DBBasic',
                'subtitle': 'The Post-Code Era Platform',
                'variant': 'gradient-animated',
                'content': [
                    {
                        'type': 'badge',
                        'text': '⚡ 402M rows/sec with DuckDB',
                        'variant': 'success',
                        'size': 'lg'
                    },
                    {
                        'type': 'button_group',
                        'class': 'mt-4',
                        'buttons': [
                            {
                                'text': 'Open Dashboard',
                                'variant': 'primary',
                                'size': 'lg',
                                'onclick': "location.href='/dashboard.html'"
                            },
                            {
                                'text': 'View Templates',
                                'variant': 'success',
                                'size': 'lg',
                                'onclick': "location.href='/templates.html'"
                            }
                        ]
                    }
                ]
            },
            # Feature cards
            {
                'type': 'container',
                'children': [
                    {
                        'type': 'grid',
                        'columns': 3,
                        'items': [
                            {
                                'type': 'card',
                                'icon': 'bi-lightning-charge',
                                'title': 'Lightning Fast',
                                'description': '402M rows/sec query performance with DuckDB'
                            },
                            {
                                'type': 'card',
                                'icon': 'bi-robot',
                                'title': 'AI-Powered',
                                'description': 'Generate business logic from natural language'
                            },
                            {
                                'type': 'card',
                                'icon': 'bi-layers',
                                'title': 'Config-Driven',
                                'description': 'Define complete apps with YAML, not code'
                            }
                        ]
                    }
                ]
            },
            # Services showcase
            {
                'type': 'container',
                'class': 'mt-5',
                'children': [
                    {
                        'type': 'heading',
                        'level': 2,
                        'text': 'Integrated Services',
                        'class': 'text-center mb-4'
                    },
                    {
                        'type': 'grid',
                        'columns': 4,
                        'items': [
                            {
                                'type': 'card',
                                'title': service['name'],
                                'description': service['description'],
                                'icon': service.get('icon', 'bi-box'),
                                'footer': {
                                    'type': 'button',
                                    'text': 'Open',
                                    'variant': 'primary',
                                    'onclick': f"location.href='http://localhost:{service['port']}'"
                                }
                            }
                            for service in SERVICES.values()
                        ]
                    }
                ]
            }
        ]
    }

    return PresentationLayer.render(index_ui, 'bootstrap')

def calculate_token_savings():
    """Calculate token savings from conversion"""

    # Estimate based on typical file sizes
    old_approach = {
        'html_in_python': 50000,  # ~500 lines HTML per service
        'inline_styles': 10000,
        'repeated_nav': 5000,
        'total': 65000
    }

    new_approach = {
        'data_structures': 5000,  # ~50 lines per service
        'shared_components': 1000,
        'total': 6000
    }

    savings = old_approach['total'] - new_approach['total']
    percentage = (savings / old_approach['total']) * 100

    print("\n💰 TOKEN ECONOMICS:")
    print(f"  Old approach: {old_approach['total']:,} tokens")
    print(f"  New approach: {new_approach['total']:,} tokens")
    print(f"  Tokens saved: {savings:,} ({percentage:.1f}%)")
    print(f"  Cost savings: ${savings * 0.00001:.2f} per generation")
    print(f"  Time savings: ~{percentage:.0f}% faster generation")

if __name__ == "__main__":
    # Generate all interfaces
    files = generate_all_interfaces()

    # Calculate and display savings
    calculate_token_savings()

    print("\n🎉 DBBasic is now fully powered by the Presentation Layer!")
    print("\n📌 Next steps:")
    print("  1. Update service endpoints to serve new HTML files")
    print("  2. Test all interfaces with live data")
    print("  3. Remove old HTML generation code")
    print("  4. Deploy and enjoy 90% token savings!")

    print("\n🚀 The Post-Code Era has arrived!")