#!/usr/bin/env python3
"""
DBBasic Bootstrap Converter - Convert data structures to Bootstrap HTML
This follows DBBasic's config-driven philosophy
"""

from typing import Dict, List, Any, Union

class BootstrapConverter:
    """Convert Python/YAML data structures to Bootstrap 5.3 HTML"""

    @staticmethod
    def convert(data: Union[Dict, List, str]) -> str:
        """Main entry point - converts any data structure to HTML"""

        if isinstance(data, str):
            return data

        if isinstance(data, list):
            return ''.join(BootstrapConverter.convert(item) for item in data)

        if isinstance(data, dict):
            # Check for component type
            component_type = data.get('type', '')

            if component_type == 'page':
                return BootstrapConverter._page(data)
            elif component_type == 'navbar':
                return BootstrapConverter._navbar(data)
            elif component_type == 'hero':
                return BootstrapConverter._hero(data)
            elif component_type == 'grid':
                return BootstrapConverter._grid(data)
            elif component_type == 'card':
                return BootstrapConverter._card(data)
            elif component_type == 'button':
                return BootstrapConverter._button(data)
            elif component_type == 'container':
                return BootstrapConverter._container(data)
            elif component_type == 'alert':
                return BootstrapConverter._alert(data)
            else:
                # Try to infer from structure
                if 'components' in data:
                    return BootstrapConverter.convert(data['components'])
                elif 'items' in data:
                    return BootstrapConverter.convert(data['items'])
                else:
                    return str(data)

        return str(data)

    @staticmethod
    def _page(data: Dict) -> str:
        """Generate complete HTML page"""
        title = data.get('title', 'DBBasic')
        components = BootstrapConverter.convert(data.get('components', []))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        .card {{ transition: transform 0.3s; }}
        .card:hover {{ transform: translateY(-5px); }}
        .hero {{ padding: 3rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
    </style>
</head>
<body>
    {components}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function deployTemplate(id) {{
            alert('Deploying template: ' + id);
        }}
        function previewTemplate(id) {{
            alert('Preview template: ' + id);
        }}
    </script>
</body>
</html>"""

    @staticmethod
    def _navbar(data: Dict) -> str:
        """Generate Bootstrap navbar"""
        brand = data.get('brand', 'DBBasic')
        links = data.get('links', [])

        nav_links = []
        for link in links:
            if isinstance(link, str):
                # Simple string becomes link with same name
                nav_links.append(f'<a class="nav-link" href="/{link.lower()}">{link}</a>')
            elif isinstance(link, dict):
                nav_links.append(f'<a class="nav-link" href="{link["url"]}">{link["text"]}</a>')

        return f"""
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">{brand}</a>
                <div class="navbar-nav ms-auto">
                    {' '.join(nav_links)}
                </div>
            </div>
        </nav>"""

    @staticmethod
    def _hero(data: Dict) -> str:
        """Generate hero section"""
        return f"""
        <div class="hero text-center">
            <div class="container">
                <h1 class="display-4">{data.get('title', '')}</h1>
                <p class="lead">{data.get('subtitle', '')}</p>
            </div>
        </div>"""

    @staticmethod
    def _grid(data: Dict) -> str:
        """Generate Bootstrap grid"""
        columns = data.get('columns', 3)
        items = data.get('items', [])

        cols_html = []
        for item in items:
            cols_html.append(f'<div class="col">{BootstrapConverter.convert(item)}</div>')

        return f"""
        <div class="container my-5">
            <div class="row row-cols-1 row-cols-md-{columns} g-4">
                {' '.join(cols_html)}
            </div>
        </div>"""

    @staticmethod
    def _card(data: Dict) -> str:
        """Generate Bootstrap card"""
        title = data.get('title', '')
        category = data.get('category', '')
        description = data.get('description', '')
        actions = data.get('actions', [])

        # Build action buttons
        action_html = []
        for action in actions:
            if isinstance(action, str):
                if action.lower() == 'deploy':
                    action_html.append(f'<button class="btn btn-success btn-sm" onclick="deployTemplate(\'{title}\')">Deploy</button>')
                elif action.lower() == 'preview':
                    action_html.append(f'<button class="btn btn-secondary btn-sm" onclick="previewTemplate(\'{title}\')">Preview</button>')
            elif isinstance(action, dict):
                action_html.append(BootstrapConverter._button(action))

        return f"""
        <div class="card h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title">{title}</h5>
                    {f'<span class="badge bg-primary">{category}</span>' if category else ''}
                </div>
                <p class="card-text">{description}</p>
            </div>
            {f'<div class="card-footer bg-transparent"><div class="d-grid gap-2 d-flex justify-content-end">{" ".join(action_html)}</div></div>' if action_html else ''}
        </div>"""

    @staticmethod
    def _button(data: Dict) -> str:
        """Generate Bootstrap button"""
        text = data.get('text', 'Button')
        variant = data.get('variant', 'primary')
        onclick = data.get('onclick', '')

        return f'<button class="btn btn-{variant}" onclick="{onclick}">{text}</button>'

    @staticmethod
    def _container(data: Dict) -> str:
        """Generate container"""
        content = BootstrapConverter.convert(data.get('content', []))
        return f'<div class="container">{content}</div>'

    @staticmethod
    def _alert(data: Dict) -> str:
        """Generate Bootstrap alert"""
        message = data.get('message', '')
        alert_type = data.get('variant', 'info')
        return f'<div class="alert alert-{alert_type}" role="alert">{message}</div>'


# Test it with a template marketplace
if __name__ == "__main__":
    # Define the page structure as data
    marketplace_page = {
        'type': 'page',
        'title': 'DBBasic - Template Marketplace',
        'components': [
            {
                'type': 'navbar',
                'brand': 'DBBasic',
                'links': ['Monitor', 'Data', 'AI Services', 'Templates']
            },
            {
                'type': 'hero',
                'title': '🛍️ Template Marketplace',
                'subtitle': 'Deploy production-ready applications instantly'
            },
            {
                'type': 'grid',
                'columns': 3,
                'items': [
                    {
                        'type': 'card',
                        'title': 'Blog Platform',
                        'category': 'CMS',
                        'description': 'Complete blog with posts, categories, SEO optimization',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'E-Commerce Store',
                        'category': 'Shop',
                        'description': 'Products, orders, inventory, payment processing',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'CRM System',
                        'category': 'Business',
                        'description': 'Contacts, leads, opportunities, sales pipeline',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'Project Manager',
                        'category': 'Productivity',
                        'description': 'Tasks, kanban boards, team collaboration',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'Social Platform',
                        'category': 'Social',
                        'description': 'User posts, comments, likes, shares',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'Help Desk',
                        'category': 'Support',
                        'description': 'Tickets, agents, knowledge base, SLA tracking',
                        'actions': ['deploy', 'preview']
                    }
                ]
            }
        ]
    }

    # Convert to HTML
    html = BootstrapConverter.convert(marketplace_page)

    # Save to file
    with open('test_marketplace.html', 'w') as f:
        f.write(html)

    print("Generated test_marketplace.html")
    print("Data structure converted to Bootstrap HTML successfully!")