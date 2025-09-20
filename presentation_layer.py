#!/usr/bin/env python3
"""
DBBasic Presentation Layer - Abstract UI representation
Converts data structures to different UI frameworks (Bootstrap, Tailwind, Material, etc.)
"""

from typing import Dict, List, Any, Union
from abc import ABC, abstractmethod
import json

# ============================================
# Abstract Presentation Layer
# ============================================

class UIRenderer(ABC):
    """Abstract base class for UI renderers"""

    @abstractmethod
    def render_page(self, data: Dict) -> str:
        pass

    @abstractmethod
    def render_navbar(self, data: Dict) -> str:
        pass

    @abstractmethod
    def render_card(self, data: Dict) -> str:
        pass

    @abstractmethod
    def render_button(self, data: Dict) -> str:
        pass

    @abstractmethod
    def render_grid(self, data: Dict) -> str:
        pass

    @abstractmethod
    def render_alert(self, data: Dict) -> str:
        pass

    def render(self, data: Union[Dict, List, str]) -> str:
        """Main render method that routes to specific renderers"""
        if isinstance(data, str):
            return data

        if isinstance(data, list):
            return ''.join(self.render(item) for item in data)

        if isinstance(data, dict):
            component_type = data.get('type', '')

            # Handle script components specially - collect them but don't render inline
            if component_type == 'script':
                if hasattr(self, 'scripts'):
                    content = data.get('content', '')
                    self.scripts.append(f'<script>{content}</script>')
                return ''  # Don't render inline

            # Route to specific renderer based on type
            if component_type == 'page':
                return self.render_page(data)
            elif component_type == 'navbar':
                return self.render_navbar(data)
            elif component_type == 'card':
                return self.render_card(data)
            elif component_type == 'button':
                return self.render_button(data)
            elif component_type == 'grid':
                return self.render_grid(data)
            elif component_type == 'alert':
                return self.render_alert(data)
            elif component_type == 'hero':
                return self.render_hero(data)
            elif component_type == 'form':
                return self.render_form(data)
            elif component_type == 'raw':
                # Raw HTML content - pass through directly
                return data.get('content', '')
            elif component_type == 'footer':
                # Footer is just raw HTML
                return data.get('content', '')
            elif 'components' in data:
                return self.render(data['components'])
            elif 'items' in data:
                return self.render(data['items'])

        return str(data)

    def render_hero(self, data: Dict) -> str:
        """Default hero implementation"""
        return f"<div><h1>{data.get('title', '')}</h1><p>{data.get('subtitle', '')}</p></div>"

    def render_form(self, data: Dict) -> str:
        """Default form implementation"""
        return "<form></form>"


# ============================================
# Bootstrap 5.3 Renderer
# ============================================

class BootstrapRenderer(UIRenderer):
    """Render to Bootstrap 5.3"""

    def __init__(self):
        self.scripts = []  # Collect scripts during rendering

    def render_page(self, data: Dict) -> str:
        title = data.get('title', 'DBBasic')
        self.scripts = []  # Reset scripts for this page
        components = self.render(data.get('components', []))

        # Collect all scripts
        scripts_html = '\n'.join(self.scripts)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    {self._get_custom_styles()}
</head>
<body>
    {components}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {scripts_html}
    {self._get_scripts()}
</body>
</html>"""

    def render_navbar(self, data: Dict) -> str:
        brand = data.get('brand', 'DBBasic')
        links = data.get('links', [])
        variant = data.get('variant', 'dark')
        search = data.get('search', True)
        user_menu = data.get('user_menu', True)

        nav_links = []
        for link in data.get('links', []):
            if isinstance(link, str):
                nav_links.append(f'<a class="nav-link" href="/{link.lower()}">{link}</a>')
            else:
                active_class = 'active' if link.get('active') else ''
                icon = f'<i class="{link.get("icon", "")} me-1"></i> ' if link.get('icon') else ''
                nav_links.append(
                    f'<li class="nav-item"><a class="nav-link {active_class}" href="{link["url"]}">{icon}{link["text"]}</a></li>'
                )

        # Professional dark navbar with gradient
        navbar_style = """
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-bottom: 2px solid #3b82f6;
        """ if variant == 'dark' else ""

        search_html = '''
        <form class="d-flex ms-auto me-3" role="search">
            <div class="input-group">
                <input class="form-control form-control-sm" type="search"
                       placeholder="Search services..." style="min-width: 200px;">
                <button class="btn btn-outline-light btn-sm" type="submit">
                    <i class="bi bi-search"></i>
                </button>
            </div>
        </form>
        ''' if search else ''

        user_menu_html = '''
        <div class="dropdown">
            <button class="btn btn-link text-white dropdown-toggle text-decoration-none"
                    type="button" data-bs-toggle="dropdown">
                <i class="bi bi-person-circle fs-5"></i>
                <span class="ms-1 d-none d-md-inline">Admin</span>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow">
                <li><h6 class="dropdown-header">Account</h6></li>
                <li><a class="dropdown-item" href="#"><i class="bi bi-person me-2"></i>Profile</a></li>
                <li><a class="dropdown-item" href="#"><i class="bi bi-gear me-2"></i>Settings</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#"><i class="bi bi-file-text me-2"></i>Documentation</a></li>
                <li><a class="dropdown-item" href="#"><i class="bi bi-github me-2"></i>GitHub</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-danger" href="#"><i class="bi bi-box-arrow-right me-2"></i>Sign out</a></li>
            </ul>
        </div>
        ''' if user_menu else ''

        return f"""
        <nav class="navbar navbar-expand-lg navbar-dark shadow-lg" style="{navbar_style}">
            <div class="container-fluid px-3">
                <a class="navbar-brand fw-bold d-flex align-items-center" href="/">
                    <div class="bg-white text-primary rounded-circle p-2 me-2">
                        <i class="bi bi-cpu-fill"></i>
                    </div>
                    <span class="fs-4">{brand}</span>
                    <span class="badge bg-success ms-2">v1.0</span>
                </a>

                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMain">
                    <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbarMain">
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0 ms-4">
                        {' '.join(nav_links)}
                    </ul>

                    {search_html}

                    <div class="d-flex align-items-center">
                        <span class="badge bg-warning text-dark me-3">
                            <i class="bi bi-lightning-fill"></i> 402M rows/sec
                        </span>
                        <button class="btn btn-link text-white position-relative me-3">
                            <i class="bi bi-bell fs-5"></i>
                            <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                                3
                            </span>
                        </button>
                        {user_menu_html}
                    </div>
                </div>
            </div>
        </nav>"""

    def render_card(self, data: Dict) -> str:
        title = data.get('title', '')
        category = data.get('category', '')
        description = data.get('description', '')
        body = data.get('body', '')
        actions = []

        for action in data.get('actions', []):
            if isinstance(action, str):
                variant = 'success' if action == 'deploy' else 'secondary'
                actions.append(f'<button class="btn btn-{variant} btn-sm" onclick="{action}Template(\'{title}\')">{action.title()}</button>')

        # If body is provided, use it; otherwise use description
        if isinstance(body, dict):
            # Body is a nested component - render it
            content = self.render(body)
        elif body:
            content = f'<p class="card-text">{body}</p>'
        elif description:
            content = f'<p class="card-text">{description}</p>'
        else:
            content = ''

        return f"""
        <div class="card h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title">{title}</h5>
                    {f'<span class="badge bg-primary">{category}</span>' if category else ''}
                </div>
                {content}
            </div>
            {f'<div class="card-footer bg-transparent"><div class="d-grid gap-2 d-flex justify-content-end">{" ".join(actions)}</div></div>' if actions else ''}
        </div>"""

    def render_button(self, data: Dict) -> str:
        return f'<button class="btn btn-{data.get("variant", "primary")}">{data.get("text", "Button")}</button>'

    def render_grid(self, data: Dict) -> str:
        columns = data.get('columns', 3)
        items = [f'<div class="col">{self.render(item)}</div>' for item in data.get('items', [])]

        return f"""
        <div class="container my-5">
            <div class="row row-cols-1 row-cols-md-{columns} g-4">
                {' '.join(items)}
            </div>
        </div>"""

    def render_alert(self, data: Dict) -> str:
        return f'<div class="alert alert-{data.get("variant", "info")}">{data.get("message", "")}</div>'

    def render_hero(self, data: Dict) -> str:
        return f"""
        <div class="bg-primary text-white text-center py-5">
            <div class="container">
                <h1 class="display-4">{data.get('title', '')}</h1>
                <p class="lead">{data.get('subtitle', '')}</p>
            </div>
        </div>"""

    def _get_custom_styles(self) -> str:
        return """
        <style>
            .card { transition: transform 0.3s; }
            .card:hover { transform: translateY(-5px); }
        </style>"""

    def _get_scripts(self) -> str:
        return """
        <script>
            function deployTemplate(id) { alert('Deploying: ' + id); }
            function previewTemplate(id) { alert('Preview: ' + id); }
        </script>"""


# ============================================
# Tailwind CSS Renderer
# ============================================

class TailwindRenderer(UIRenderer):
    """Render to Tailwind CSS"""

    def render_page(self, data: Dict) -> str:
        title = data.get('title', 'DBBasic')
        components = self.render(data.get('components', []))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    {components}
    <script>
        function deployTemplate(id) {{ alert('Deploying: ' + id); }}
        function previewTemplate(id) {{ alert('Preview: ' + id); }}
    </script>
</body>
</html>"""

    def render_navbar(self, data: Dict) -> str:
        brand = data.get('brand', 'DBBasic')
        links = []
        for link in data.get('links', []):
            if isinstance(link, str):
                links.append(f'<a class="px-3 py-2 text-gray-700 hover:text-gray-900" href="/{link.lower()}">{link}</a>')

        return f"""
        <nav class="bg-white shadow-lg">
            <div class="container mx-auto px-4">
                <div class="flex justify-between items-center py-4">
                    <span class="text-xl font-bold">{brand}</span>
                    <div class="flex space-x-4">
                        {' '.join(links)}
                    </div>
                </div>
            </div>
        </nav>"""

    def render_card(self, data: Dict) -> str:
        title = data.get('title', '')
        category = data.get('category', '')
        description = data.get('description', '')
        actions = []

        for action in data.get('actions', []):
            if isinstance(action, str):
                color = 'green' if action == 'deploy' else 'gray'
                actions.append(f'<button class="bg-{color}-500 hover:bg-{color}-600 text-white px-4 py-2 rounded" onclick="{action}Template(\'{title}\')">{action.title()}</button>')

        return f"""
        <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-xl font-semibold">{title}</h3>
                {f'<span class="bg-blue-500 text-white px-2 py-1 rounded text-sm">{category}</span>' if category else ''}
            </div>
            <p class="text-gray-600 mb-4">{description}</p>
            {f'<div class="flex justify-end space-x-2">{" ".join(actions)}</div>' if actions else ''}
        </div>"""

    def render_button(self, data: Dict) -> str:
        colors = {'primary': 'blue', 'success': 'green', 'danger': 'red'}
        color = colors.get(data.get('variant', 'primary'), 'blue')
        return f'<button class="bg-{color}-500 hover:bg-{color}-600 text-white px-4 py-2 rounded">{data.get("text", "Button")}</button>'

    def render_grid(self, data: Dict) -> str:
        columns = data.get('columns', 3)
        items = [self.render(item) for item in data.get('items', [])]

        return f"""
        <div class="container mx-auto px-4 my-8">
            <div class="grid grid-cols-1 md:grid-cols-{columns} gap-6">
                {' '.join(items)}
            </div>
        </div>"""

    def render_alert(self, data: Dict) -> str:
        colors = {'info': 'blue', 'success': 'green', 'warning': 'yellow', 'danger': 'red'}
        color = colors.get(data.get('variant', 'info'), 'blue')
        return f'<div class="bg-{color}-100 border border-{color}-400 text-{color}-700 px-4 py-3 rounded">{data.get("message", "")}</div>'

    def render_hero(self, data: Dict) -> str:
        return f"""
        <div class="bg-gradient-to-r from-blue-500 to-purple-600 text-white text-center py-16">
            <div class="container mx-auto px-4">
                <h1 class="text-5xl font-bold mb-4">{data.get('title', '')}</h1>
                <p class="text-xl">{data.get('subtitle', '')}</p>
            </div>
        </div>"""


# ============================================
# Presentation Manager
# ============================================

class PresentationLayer:
    """Manages different UI renderers"""

    RENDERERS = {
        'bootstrap': BootstrapRenderer(),
        'tailwind': TailwindRenderer(),
    }

    @classmethod
    def initialize_extended(cls):
        """Initialize with extended renderers"""
        try:
            from bootstrap_components import ExtendedBootstrapRenderer
            cls.RENDERERS['bootstrap'] = ExtendedBootstrapRenderer()
            cls.RENDERERS['bootstrap_extended'] = ExtendedBootstrapRenderer()
        except ImportError:
            pass  # Use basic renderer if extended not available

    @staticmethod
    def render(data: Union[Dict, List, str], framework: str = 'bootstrap') -> str:
        """Render data using specified framework"""
        renderer = PresentationLayer.RENDERERS.get(framework)
        if not renderer:
            raise ValueError(f"Unknown framework: {framework}. Available: {list(PresentationLayer.RENDERERS.keys())}")

        return renderer.render(data)

    @staticmethod
    def add_renderer(name: str, renderer: UIRenderer):
        """Add a custom renderer"""
        PresentationLayer.RENDERERS[name] = renderer


# ============================================
# Test the presentation layer
# ============================================

if __name__ == "__main__":
    # Define UI structure as data (framework-agnostic)
    ui_structure = {
        'type': 'page',
        'title': 'DBBasic Template Marketplace',
        'components': [
            {
                'type': 'navbar',
                'brand': 'DBBasic',
                'links': ['Monitor', 'Data', 'Templates']
            },
            {
                'type': 'hero',
                'title': 'Template Marketplace',
                'subtitle': 'Deploy apps instantly'
            },
            {
                'type': 'grid',
                'columns': 3,
                'items': [
                    {
                        'type': 'card',
                        'title': 'Blog',
                        'category': 'CMS',
                        'description': 'Full-featured blog platform',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'Shop',
                        'category': 'E-Commerce',
                        'description': 'Online store with payments',
                        'actions': ['deploy', 'preview']
                    },
                    {
                        'type': 'card',
                        'title': 'CRM',
                        'category': 'Business',
                        'description': 'Customer relationship manager',
                        'actions': ['deploy', 'preview']
                    }
                ]
            }
        ]
    }

    # Render to Bootstrap
    bootstrap_html = PresentationLayer.render(ui_structure, 'bootstrap')
    with open('test_bootstrap.html', 'w') as f:
        f.write(bootstrap_html)
    print("✅ Generated test_bootstrap.html")

    # Render to Tailwind
    tailwind_html = PresentationLayer.render(ui_structure, 'tailwind')
    with open('test_tailwind.html', 'w') as f:
        f.write(tailwind_html)
    print("✅ Generated test_tailwind.html")

    print("\nSame data structure rendered to different frameworks!")
    print("Open test_bootstrap.html and test_tailwind.html to see the difference")