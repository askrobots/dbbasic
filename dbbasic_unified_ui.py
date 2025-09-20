#!/usr/bin/env python3
"""
DBBasic Unified UI System
Master layout and navigation for all services
"""

from typing import Dict, List, Any, Optional
from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer

# Initialize presentation layer
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())

# Service registry with ports and status
SERVICES = {
    'monitor': {
        'name': 'Monitor',
        'port': 8004,
        'icon': 'bi-activity',
        'description': 'Real-time service monitoring',
        'status': 'running'
    },
    'data': {
        'name': 'Data',
        'port': 8005,
        'icon': 'bi-database',
        'description': 'CRUD Engine - 402M rows/sec',
        'status': 'running'
    },
    'ai_services': {
        'name': 'AI Services',
        'port': 8003,
        'icon': 'bi-robot',
        'description': 'AI-powered service builder',
        'status': 'running'
    },
    'event_store': {
        'name': 'Event Store',
        'port': 8007,
        'icon': 'bi-journal-text',
        'description': 'Event sourcing & audit trails',
        'status': 'running'
    },
    'test_runner': {
        'name': 'Test Runner',
        'port': 8006,
        'icon': 'bi-speedometer2',
        'description': 'Testing at 402M rows/sec',
        'status': 'running'
    },
    'templates': {
        'name': 'Templates',
        'port': 8005,
        'path': '/templates',
        'icon': 'bi-shop',
        'description': 'Template marketplace',
        'status': 'running'
    }
}

def get_unified_navigation(active_service: str = None) -> Dict:
    """Generate unified navigation bar"""
    links = []
    for key, service in SERVICES.items():
        url = f"http://localhost:{service['port']}"
        if 'path' in service:
            url += service['path']

        links.append({
            'text': service['name'],
            'url': url,
            'active': key == active_service,
            'icon': service.get('icon', '')
        })

    return {
        'type': 'navbar',
        'brand': 'DBBasic',
        'variant': 'dark',
        'links': links,
        'extras': [
            {'type': 'badge', 'text': '⚡ 402M rows/sec', 'variant': 'success'}
        ]
    }

def get_master_layout(
    title: str,
    service_name: str,
    content: List[Dict],
    scripts: Optional[List[Dict]] = None,
    styles: Optional[List[Dict]] = None
) -> Dict:
    """Generate master layout for any DBBasic service"""

    # Build the page structure
    page = {
        'type': 'page',
        'title': f'{title} - DBBasic',
        'components': [
            # Unified navigation
            get_unified_navigation(service_name),

            # Service header (optional)
            {
                'type': 'container',
                'fluid': True,
                'class': 'bg-light py-3 mb-4',
                'children': [
                    {
                        'type': 'container',
                        'children': [
                            {
                                'type': 'breadcrumb',
                                'items': [
                                    {'text': 'DBBasic', 'url': '/'},
                                    {'text': SERVICES.get(service_name, {}).get('name', service_name), 'active': True}
                                ]
                            }
                        ]
                    }
                ]
            },

            # Main content area
            {
                'type': 'container',
                'fluid': True,
                'children': content
            },

            # Footer
            get_footer()
        ]
    }

    # Add scripts if provided
    if scripts:
        page['components'].extend(scripts)

    # Add styles if provided
    if styles:
        # Insert styles after navbar
        page['components'].insert(1, styles)

    return page

def get_footer() -> Dict:
    """Generate professional unified footer"""
    # Build service links
    service_links = []
    for key, service in SERVICES.items():
        url = f"http://localhost:{service['port']}"
        if 'path' in service:
            url += service['path']
        icon = service.get('icon', 'bi-circle')
        service_links.append(
            f'<li class="mb-2"><a href="{url}" class="text-decoration-none text-light opacity-75">'
            f'<i class="{icon} me-2"></i>{service["name"]}</a></li>'
        )

    return {
        'type': 'raw',
        'content': f'''
        <footer class="mt-auto" style="background: linear-gradient(135deg, #1a1a2e 0%, #0f172a 100%); margin-top: 5rem !important;">
            <div class="container-fluid py-5">
                <div class="row g-4 px-4">
                    <!-- Brand Section -->
                    <div class="col-lg-4">
                        <div class="d-flex align-items-center mb-3">
                            <div class="bg-primary rounded-circle p-2 me-2">
                                <i class="bi bi-cpu-fill text-white fs-5"></i>
                            </div>
                            <h4 class="text-white mb-0">DBBasic</h4>
                            <span class="badge bg-success ms-2">v1.0</span>
                        </div>
                        <p class="text-light opacity-75">
                            Revolutionary config-driven platform. Build production apps with YAML & AI.
                        </p>
                        <div class="d-flex gap-2 mt-3">
                            <a href="#" class="btn btn-outline-light btn-sm">
                                <i class="bi bi-github"></i> GitHub
                            </a>
                            <a href="#" class="btn btn-outline-light btn-sm">
                                <i class="bi bi-book"></i> Docs
                            </a>
                        </div>
                    </div>

                    <!-- Services -->
                    <div class="col-lg-2 col-md-6">
                        <h6 class="text-white mb-3">Services</h6>
                        <ul class="list-unstyled">
                            {''.join(service_links)}
                        </ul>
                    </div>

                    <!-- Resources -->
                    <div class="col-lg-3 col-md-6">
                        <h6 class="text-white mb-3">Resources</h6>
                        <ul class="list-unstyled">
                            <li class="mb-2">
                                <a href="#" class="text-decoration-none text-light opacity-75">
                                    <i class="bi bi-file-text me-2"></i>Documentation
                                </a>
                            </li>
                            <li class="mb-2">
                                <a href="#" class="text-decoration-none text-light opacity-75">
                                    <i class="bi bi-code-square me-2"></i>API Reference
                                </a>
                            </li>
                            <li class="mb-2">
                                <a href="#" class="text-decoration-none text-light opacity-75">
                                    <i class="bi bi-play-circle me-2"></i>Tutorials
                                </a>
                            </li>
                        </ul>
                    </div>

                    <!-- Stats -->
                    <div class="col-lg-3">
                        <h6 class="text-white mb-3">Performance</h6>
                        <div class="d-flex flex-column gap-2">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-lightning-fill text-warning me-2"></i>
                                <span class="text-light opacity-75">402M rows/sec</span>
                            </div>
                            <div class="d-flex align-items-center">
                                <i class="bi bi-hdd-stack text-info me-2"></i>
                                <span class="text-light opacity-75">DuckDB Engine</span>
                            </div>
                            <div class="d-flex align-items-center">
                                <i class="bi bi-gear-fill text-success me-2"></i>
                                <span class="text-light opacity-75">90% Token Reduction</span>
                            </div>
                            <div class="d-flex align-items-center">
                                <i class="bi bi-magic text-primary me-2"></i>
                                <span class="text-light opacity-75">AI-Powered</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bottom Bar -->
            <div class="border-top border-dark bg-black bg-opacity-25">
                <div class="container-fluid py-3">
                    <div class="text-center">
                        <p class="text-light opacity-50 mb-0 small">
                            © 2024 DBBasic - Post-Code Era Platform • Built with <i class="bi bi-heart-fill text-danger"></i> for developers
                        </p>
                    </div>
                </div>
            </div>
        </footer>
        '''
    }

def get_service_dashboard() -> Dict:
    """Generate main service dashboard"""
    return get_master_layout(
        title='Services Dashboard',
        service_name='dashboard',
        content=[
            # Hero section
            {
                'type': 'hero',
                'title': 'DBBasic Platform',
                'subtitle': 'All services running at peak performance'
            },

            # Service cards grid
            {
                'type': 'grid',
                'columns': 3,
                'items': [
                    {
                        'type': 'card',
                        'id': f'{key}-card',
                        'title': service['name'],
                        'category': f'Port {service["port"]}',
                        'description': service['description'],
                        'footer': [
                            {
                                'type': 'badge',
                                'text': 'Running' if service['status'] == 'running' else 'Stopped',
                                'variant': 'success' if service['status'] == 'running' else 'danger'
                            },
                            {
                                'type': 'button',
                                'text': 'Open',
                                'variant': 'primary',
                                'onclick': f"window.open('http://localhost:{service['port']}')"
                            }
                        ]
                    }
                    for key, service in SERVICES.items()
                ]
            }
        ]
    )

# Service-specific layouts
def get_crud_engine_layout(content: List[Dict]) -> Dict:
    """Layout for CRUD Engine pages"""
    return get_master_layout(
        title='Data Service',
        service_name='data',
        content=content,
        scripts=[{
            'type': 'script',
            'content': '''
                // CRUD Engine specific scripts
                console.log("CRUD Engine initialized");
            '''
        }]
    )

def get_ai_service_layout(content: List[Dict]) -> Dict:
    """Layout for AI Service Builder pages"""
    return get_master_layout(
        title='AI Service Builder',
        service_name='ai_services',
        content=content,
        scripts=[{
            'type': 'script',
            'content': '''
                // AI Service specific scripts
                console.log("AI Service Builder initialized");
            '''
        }]
    )

def get_monitor_layout(content: List[Dict]) -> Dict:
    """Layout for Real-time Monitor"""
    return get_master_layout(
        title='Real-time Monitor',
        service_name='monitor',
        content=content,
        scripts=[{
            'type': 'script',
            'content': '''
                // WebSocket connection for real-time updates
                let ws = new WebSocket('ws://localhost:8004/ws');
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    updateMetrics(data);
                };
            '''
        }]
    )

def get_event_store_layout(content: List[Dict]) -> Dict:
    """Layout for Event Store"""
    return get_master_layout(
        title='Event Store',
        service_name='event_store',
        content=content
    )

# Convert all views to unified layout
def convert_crud_engine_views():
    """Convert all CRUD Engine views to use unified layout"""

    # Main CRUD dashboard
    crud_dashboard = get_crud_engine_layout([
        {
            'type': 'hero',
            'title': 'Data Service',
            'subtitle': 'Config-driven CRUD at 402M rows/sec'
        },
        {
            'type': 'grid',
            'columns': 2,
            'items': [
                {
                    'type': 'card',
                    'title': 'Resources',
                    'description': 'Manage your data resources',
                    'actions': [
                        {'type': 'button', 'text': 'View Resources', 'onclick': "location.href='/resources'"}
                    ]
                },
                {
                    'type': 'card',
                    'title': 'Templates',
                    'description': 'Browse and deploy templates',
                    'actions': [
                        {'type': 'button', 'text': 'Template Marketplace', 'onclick': "location.href='/templates'"}
                    ]
                }
            ]
        }
    ])

    # Template marketplace
    template_marketplace = get_crud_engine_layout([
        {
            'type': 'hero',
            'title': '🛍️ Template Marketplace',
            'subtitle': 'Deploy production-ready applications instantly'
        },
        {
            'type': 'grid',
            'columns': 3,
            'items': []  # Templates loaded dynamically
        }
    ])

    return {
        'dashboard': crud_dashboard,
        'templates': template_marketplace
    }

# Example: Convert a static mockup
def convert_static_mockup(mockup_name: str) -> Dict:
    """Convert static HTML mockups to data structures"""

    if mockup_name == 'dashboard':
        return get_master_layout(
            title='Dashboard Mockup',
            service_name='dashboard',
            content=[
                {
                    'type': 'alert',
                    'message': 'This is a converted mockup using the presentation layer',
                    'variant': 'info'
                },
                # Add mockup content here
            ]
        )

    # Convert other mockups...
    return {}

# Generate all layouts
if __name__ == "__main__":
    # Generate service dashboard
    dashboard_html = PresentationLayer.render(get_service_dashboard(), 'bootstrap')
    with open('dbbasic_dashboard.html', 'w') as f:
        f.write(dashboard_html)

    # Generate CRUD views
    crud_views = convert_crud_engine_views()
    for name, view in crud_views.items():
        html = PresentationLayer.render(view, 'bootstrap')
        with open(f'crud_{name}.html', 'w') as f:
            f.write(html)

    print("✅ Generated unified DBBasic UI")
    print("\nUnified features:")
    print("- Consistent navigation across all services")
    print("- Master layout template")
    print("- Service-specific layouts")
    print("- Unified footer")
    print("- Clean data structures for everything")
    print("\nAll services now share the same UI system!")