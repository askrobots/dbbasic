#!/usr/bin/env python3
"""
DBBasic Component Marketplace
Reusable UI components that can be shared and imported
"""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path

class ComponentMarketplace:
    """Marketplace for sharing and discovering UI components"""

    def __init__(self):
        self.components = {}
        self.categories = {
            'navigation': [],
            'heroes': [],
            'cards': [],
            'forms': [],
            'tables': [],
            'dashboards': [],
            'charts': [],
            'layouts': []
        }
        self.load_built_in_components()

    def load_built_in_components(self):
        """Load built-in component library"""

        # Navigation Components
        self.register_component({
            'id': 'unified-nav',
            'name': 'Unified Navigation',
            'category': 'navigation',
            'description': 'DBBasic unified navigation with service links',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'navbar',
                'brand': 'DBBasic',
                'variant': 'dark',
                'links': [
                    {'text': 'Monitor', 'url': 'http://localhost:8004'},
                    {'text': 'Data', 'url': 'http://localhost:8005'},
                    {'text': 'AI Services', 'url': 'http://localhost:8003'},
                    {'text': 'Events', 'url': 'http://localhost:8006'}
                ]
            }
        })

        # Dashboard Components
        self.register_component({
            'id': 'metrics-dashboard',
            'name': 'Metrics Dashboard',
            'category': 'dashboards',
            'description': 'Real-time metrics dashboard with 4 KPIs',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'grid',
                'columns': 4,
                'items': [
                    {
                        'type': 'card',
                        'id': 'metric-1',
                        'body': {
                            'type': 'metric',
                            'label': 'Total Users',
                            'value': '0',
                            'icon': 'bi-people'
                        }
                    },
                    {
                        'type': 'card',
                        'id': 'metric-2',
                        'body': {
                            'type': 'metric',
                            'label': 'Revenue',
                            'value': '$0',
                            'icon': 'bi-currency-dollar'
                        }
                    },
                    {
                        'type': 'card',
                        'id': 'metric-3',
                        'body': {
                            'type': 'metric',
                            'label': 'Orders',
                            'value': '0',
                            'icon': 'bi-cart'
                        }
                    },
                    {
                        'type': 'card',
                        'id': 'metric-4',
                        'body': {
                            'type': 'metric',
                            'label': 'Performance',
                            'value': '100%',
                            'icon': 'bi-speedometer2'
                        }
                    }
                ]
            }
        })

        # Form Components
        self.register_component({
            'id': 'user-registration',
            'name': 'User Registration Form',
            'category': 'forms',
            'description': 'Complete user registration form with validation',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'form',
                'id': 'registration-form',
                'fields': [
                    {
                        'type': 'input',
                        'name': 'username',
                        'label': 'Username',
                        'placeholder': 'Choose a username',
                        'required': True
                    },
                    {
                        'type': 'input',
                        'input_type': 'email',
                        'name': 'email',
                        'label': 'Email Address',
                        'placeholder': 'your@email.com',
                        'required': True
                    },
                    {
                        'type': 'input',
                        'input_type': 'password',
                        'name': 'password',
                        'label': 'Password',
                        'placeholder': 'Min 8 characters',
                        'required': True
                    },
                    {
                        'type': 'checkbox',
                        'name': 'terms',
                        'label': 'I agree to the terms and conditions',
                        'required': True
                    }
                ],
                'submit': {
                    'text': 'Create Account',
                    'variant': 'primary'
                }
            }
        })

        # Card Components
        self.register_component({
            'id': 'service-card',
            'name': 'Service Status Card',
            'category': 'cards',
            'description': 'Card showing service status and metrics',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'card',
                'title': '{{service_name}}',
                'body': {
                    'type': 'div',
                    'children': [
                        {'type': 'badge', 'text': '{{status}}', 'variant': 'success'},
                        {'type': 'p', 'text': '{{description}}'},
                        {
                            'type': 'div',
                            'class': 'mt-3',
                            'children': [
                                {'type': 'small', 'text': 'Port: {{port}}'},
                                {'type': 'small', 'text': ' | '},
                                {'type': 'small', 'text': 'Uptime: {{uptime}}'}
                            ]
                        }
                    ]
                },
                'footer': {
                    'type': 'button_group',
                    'buttons': [
                        {'text': 'View', 'variant': 'primary', 'size': 'sm'},
                        {'text': 'Restart', 'variant': 'warning', 'size': 'sm'}
                    ]
                }
            }
        })

        # Table Components
        self.register_component({
            'id': 'data-table',
            'name': 'Interactive Data Table',
            'category': 'tables',
            'description': 'Sortable, filterable data table',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'div',
                'children': [
                    {
                        'type': 'div',
                        'class': 'table-controls mb-3',
                        'children': [
                            {
                                'type': 'input',
                                'id': 'table-search',
                                'placeholder': 'Search...',
                                'class': 'form-control'
                            }
                        ]
                    },
                    {
                        'type': 'table',
                        'id': 'data-table',
                        'datatable': True,
                        'headers': ['ID', 'Name', 'Status', 'Actions'],
                        'rows': []
                    }
                ]
            }
        })

        # Hero Components
        self.register_component({
            'id': 'gradient-hero',
            'name': 'Gradient Hero Section',
            'category': 'heroes',
            'description': 'Eye-catching hero with gradient background',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'hero',
                'title': '{{title}}',
                'subtitle': '{{subtitle}}',
                'variant': 'gradient-purple',
                'content': [
                    {
                        'type': 'button_group',
                        'buttons': [
                            {'text': 'Get Started', 'variant': 'primary', 'size': 'lg'},
                            {'text': 'Learn More', 'variant': 'outline-light', 'size': 'lg'}
                        ]
                    }
                ]
            }
        })

        # Chart Components
        self.register_component({
            'id': 'line-chart',
            'name': 'Line Chart Component',
            'category': 'charts',
            'description': 'Interactive line chart with real-time updates',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'card',
                'title': '{{chart_title}}',
                'body': {
                    'type': 'chart',
                    'id': '{{chart_id}}',
                    'chartType': 'line',
                    'data': {
                        'labels': [],
                        'datasets': []
                    }
                }
            }
        })

        # Layout Components
        self.register_component({
            'id': 'two-column-layout',
            'name': 'Two Column Layout',
            'category': 'layouts',
            'description': 'Responsive two-column layout',
            'author': 'DBBasic Team',
            'version': '1.0.0',
            'frameworks': ['bootstrap', 'tailwind'],
            'data': {
                'type': 'div',
                'class': 'row',
                'children': [
                    {
                        'type': 'div',
                        'class': 'col-md-8',
                        'id': 'main-content',
                        'children': []
                    },
                    {
                        'type': 'div',
                        'class': 'col-md-4',
                        'id': 'sidebar',
                        'children': []
                    }
                ]
            }
        })

    def register_component(self, component: Dict):
        """Register a new component in the marketplace"""
        comp_id = component['id']
        category = component['category']

        self.components[comp_id] = component

        if category in self.categories:
            self.categories[category].append(comp_id)

        return comp_id

    def get_component(self, component_id: str) -> Optional[Dict]:
        """Get a component by ID"""
        return self.components.get(component_id)

    def search_components(self, query: str = None, category: str = None) -> List[Dict]:
        """Search for components"""
        results = []

        for comp_id, component in self.components.items():
            # Filter by category
            if category and component['category'] != category:
                continue

            # Filter by search query
            if query:
                search_text = f"{component['name']} {component['description']}".lower()
                if query.lower() not in search_text:
                    continue

            results.append(component)

        return results

    def use_component(self, component_id: str, **params) -> Dict:
        """Use a component with parameter substitution"""
        component = self.get_component(component_id)
        if not component:
            raise ValueError(f"Component {component_id} not found")

        # Deep copy the component data
        import copy
        data = copy.deepcopy(component['data'])

        # Replace template variables
        data_str = json.dumps(data)
        for key, value in params.items():
            data_str = data_str.replace(f'{{{{{key}}}}}', str(value))

        return json.loads(data_str)

    def export_component(self, component_id: str, format: str = 'json') -> str:
        """Export a component for sharing"""
        component = self.get_component(component_id)
        if not component:
            raise ValueError(f"Component {component_id} not found")

        if format == 'json':
            return json.dumps(component, indent=2)
        elif format == 'python':
            return f"component = {repr(component)}"
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_component(self, data: str, format: str = 'json') -> str:
        """Import a component from external source"""
        if format == 'json':
            component = json.loads(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return self.register_component(component)

    def generate_showcase_page(self) -> Dict:
        """Generate a showcase page for all components"""
        from dbbasic_unified_ui import get_master_layout

        showcase_items = []

        for category, component_ids in self.categories.items():
            if not component_ids:
                continue

            category_section = {
                'type': 'div',
                'children': [
                    {'type': 'h2', 'text': category.title()},
                    {
                        'type': 'grid',
                        'columns': 2,
                        'items': []
                    }
                ]
            }

            for comp_id in component_ids:
                component = self.get_component(comp_id)
                if component:
                    card = {
                        'type': 'card',
                        'title': component['name'],
                        'description': component['description'],
                        'footer': {
                            'type': 'div',
                            'children': [
                                {'type': 'small', 'text': f"v{component['version']} by {component['author']}"},
                                {
                                    'type': 'button_group',
                                    'class': 'mt-2',
                                    'buttons': [
                                        {
                                            'text': 'Use',
                                            'variant': 'primary',
                                            'size': 'sm',
                                            'onclick': f"useComponent('{comp_id}')"
                                        },
                                        {
                                            'text': 'Preview',
                                            'variant': 'info',
                                            'size': 'sm',
                                            'onclick': f"previewComponent('{comp_id}')"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                    category_section['children'][1]['items'].append(card)

            showcase_items.append(category_section)

        return get_master_layout(
            title='Component Marketplace',
            service_name='marketplace',
            content=[
                {
                    'type': 'hero',
                    'title': '🎨 Component Marketplace',
                    'subtitle': 'Reusable UI components for rapid development',
                    'variant': 'gradient-purple'
                },
                {
                    'type': 'alert',
                    'message': f'Browse {len(self.components)} pre-built components across {len(self.categories)} categories',
                    'variant': 'info'
                },
                *showcase_items
            ]
        )


# Global marketplace instance
marketplace = ComponentMarketplace()


def create_custom_component(name: str, description: str, data: Dict) -> str:
    """Helper to create custom components"""
    component = {
        'id': name.lower().replace(' ', '-'),
        'name': name,
        'category': 'custom',
        'description': description,
        'author': 'User',
        'version': '1.0.0',
        'frameworks': ['bootstrap', 'tailwind'],
        'data': data
    }

    return marketplace.register_component(component)


# Example usage
if __name__ == "__main__":
    from presentation_layer import PresentationLayer
    from bootstrap_components import ExtendedBootstrapRenderer

    # Initialize
    PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())

    # Use a component from marketplace
    nav_data = marketplace.use_component('unified-nav')
    metrics_data = marketplace.use_component(
        'metrics-dashboard',
        metric_1_value='1,234',
        metric_2_value='$45,678'
    )

    # Create a page using marketplace components
    page = {
        'type': 'page',
        'title': 'Component Marketplace Demo',
        'components': [
            nav_data,
            metrics_data,
            marketplace.use_component(
                'gradient-hero',
                title='Component Marketplace',
                subtitle='Build faster with reusable components'
            )
        ]
    }

    # Render
    html = PresentationLayer.render(page, 'bootstrap')

    # Generate showcase
    showcase_page = marketplace.generate_showcase_page()
    showcase_html = PresentationLayer.render(showcase_page, 'bootstrap')

    with open('static/marketplace.html', 'w') as f:
        f.write(showcase_html)

    print("✅ Component Marketplace created!")
    print(f"\n📦 Available components: {len(marketplace.components)}")
    print("\n🎨 Categories:")
    for category, items in marketplace.categories.items():
        if items:
            print(f"  • {category}: {len(items)} components")

    print("\n💡 Usage example:")
    print("  nav = marketplace.use_component('unified-nav')")
    print("  html = PresentationLayer.render(nav, 'bootstrap')")
    print("\n📄 Showcase page generated at static/marketplace.html")