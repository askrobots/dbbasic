#!/usr/bin/env python3
"""
DBBasic HTML Builders - Experiments in data-to-Bootstrap conversion
Let's try different approaches and see what feels most natural
"""

import json
from typing import Dict, List, Any, Optional

# ============================================
# APPROACH 1: Simple dict-to-Bootstrap mapping
# ============================================

def dict_to_bootstrap(data: Dict[str, Any]) -> str:
    """Convert a dict structure directly to Bootstrap HTML"""
    component_type = data.get('type', 'div')

    if component_type == 'page':
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{data.get('title', 'DBBasic')}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
</head>
<body>
    {dict_to_bootstrap(data.get('body', {}))}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    elif component_type == 'navbar':
        items = ''.join([f'<a class="nav-link" href="{item["url"]}">{item["text"]}</a>'
                        for item in data.get('items', [])])
        return f"""<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">{data.get('brand', 'DBBasic')}</a>
        <div class="navbar-nav ms-auto">{items}</div>
    </div>
</nav>"""

    elif component_type == 'card':
        return f"""<div class="card">
    <div class="card-body">
        <h5 class="card-title">{data.get('title', '')}</h5>
        <p class="card-text">{data.get('text', '')}</p>
        {dict_to_bootstrap(data.get('footer', {})) if 'footer' in data else ''}
    </div>
</div>"""

    elif component_type == 'button':
        return f"""<button class="btn btn-{data.get('variant', 'primary')}" {data.get('attrs', '')}>
    {data.get('text', 'Button')}
</button>"""

    elif component_type == 'grid':
        cols = ''.join([f'<div class="col">{dict_to_bootstrap(col)}</div>'
                       for col in data.get('columns', [])])
        return f'<div class="row">{cols}</div>'

    elif component_type == 'container':
        children = ''.join([dict_to_bootstrap(child) for child in data.get('children', [])])
        return f'<div class="container">{children}</div>'

    else:
        # Default div with optional content
        return f'<div>{data.get("content", "")}</div>'


# ============================================
# APPROACH 2: List-based component builder
# ============================================

def build_from_list(components: List) -> str:
    """Build HTML from a list of component definitions"""
    html = []

    for comp in components:
        if isinstance(comp, str):
            html.append(comp)
        elif isinstance(comp, dict):
            html.append(dict_to_bootstrap(comp))
        elif isinstance(comp, list):
            # Handle nested lists as containers
            html.append(f'<div>{build_from_list(comp)}</div>')
        elif isinstance(comp, tuple):
            # Tuples as (tag, attrs, content)
            tag, attrs, content = comp
            attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items()) if isinstance(attrs, dict) else attrs
            html.append(f'<{tag} {attr_str}>{content}</{tag}>')

    return ''.join(html)


# ============================================
# APPROACH 3: Functional composition
# ============================================

def page(**kwargs):
    """Create a page structure"""
    return {
        'type': 'page',
        'title': kwargs.get('title', 'DBBasic'),
        'body': kwargs.get('body', {})
    }

def navbar(brand: str, *items):
    """Create a navbar"""
    return {
        'type': 'navbar',
        'brand': brand,
        'items': [{'text': item[0], 'url': item[1]} for item in items]
    }

def card(title: str, text: str, **kwargs):
    """Create a card"""
    return {
        'type': 'card',
        'title': title,
        'text': text,
        **kwargs
    }

def button(text: str, variant: str = 'primary', **attrs):
    """Create a button"""
    attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    return {
        'type': 'button',
        'text': text,
        'variant': variant,
        'attrs': attr_str
    }

def grid(*columns):
    """Create a grid"""
    return {
        'type': 'grid',
        'columns': list(columns)
    }

def container(*children):
    """Create a container"""
    return {
        'type': 'container',
        'children': list(children)
    }


# ============================================
# APPROACH 4: JSON schema to Bootstrap
# ============================================

def json_schema_to_form(schema: Dict[str, Any]) -> str:
    """Convert JSON schema to Bootstrap form"""
    form_fields = []

    for field_name, field_def in schema.get('properties', {}).items():
        field_type = field_def.get('type', 'string')

        if field_type == 'string':
            input_type = 'text'
            if 'format' in field_def:
                if field_def['format'] == 'email':
                    input_type = 'email'
                elif field_def['format'] == 'date':
                    input_type = 'date'
        elif field_type == 'number':
            input_type = 'number'
        elif field_type == 'boolean':
            input_type = 'checkbox'
        else:
            input_type = 'text'

        form_fields.append(f"""
        <div class="mb-3">
            <label for="{field_name}" class="form-label">{field_def.get('title', field_name)}</label>
            <input type="{input_type}" class="form-control" id="{field_name}" name="{field_name}"
                   {'required' if field_name in schema.get('required', []) else ''}>
            {f'<div class="form-text">{field_def["description"]}</div>' if 'description' in field_def else ''}
        </div>
        """)

    return f'<form>{"".join(form_fields)}<button type="submit" class="btn btn-primary">Submit</button></form>'


# ============================================
# APPROACH 5: Template marketplace specific
# ============================================

def render_template_marketplace(templates: List[Dict]) -> str:
    """Render template marketplace using functional composition"""

    # Build cards for each template
    cards = []
    for template in templates:
        cards.append(card(
            title=template['name'],
            text=f"{template['description']} • {template['fields_count']} fields",
            footer={
                'type': 'container',
                'children': [
                    button('Preview', 'secondary', onclick=f"previewTemplate('{template['id']}')"),
                    button('Deploy', 'success', onclick=f"deployTemplate('{template['id']}')")
                ]
            }
        ))

    # Build the page structure
    page_structure = page(
        title="Template Marketplace",
        body=container(
            navbar("DBBasic",
                   ("Monitor", "http://localhost:8004"),
                   ("Data", "http://localhost:8005"),
                   ("Templates", "/templates")),
            {'type': 'container', 'children': [
                '<h1 class="text-center my-4">Template Marketplace</h1>',
                '<p class="text-center text-muted mb-5">Deploy production-ready apps instantly</p>',
                grid(*cards)
            ]}
        )
    )

    return dict_to_bootstrap(page_structure)


# ============================================
# APPROACH 6: Pure data transformation
# ============================================

class BootstrapRenderer:
    """Render data structures as Bootstrap HTML"""

    @staticmethod
    def render(data: Any) -> str:
        """Main render method that handles any data type"""
        if isinstance(data, dict):
            return BootstrapRenderer._render_dict(data)
        elif isinstance(data, list):
            return ''.join(BootstrapRenderer.render(item) for item in data)
        elif isinstance(data, str):
            return data
        else:
            return str(data)

    @staticmethod
    def _render_dict(data: Dict) -> str:
        """Render dict based on its structure"""
        # Check for special keys that indicate component types
        if '_component' in data:
            return BootstrapRenderer._render_component(data)
        elif '_tag' in data:
            tag = data['_tag']
            attrs = data.get('_attrs', {})
            children = data.get('_children', [])
            attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
            content = BootstrapRenderer.render(children)
            return f'<{tag} {attr_str}>{content}</{tag}>'
        else:
            # Try to infer component from keys
            if 'title' in data and 'text' in data:
                return BootstrapRenderer._render_card(data)
            elif 'columns' in data:
                return BootstrapRenderer._render_grid(data)
            else:
                return str(data)

    @staticmethod
    def _render_component(data: Dict) -> str:
        """Render specific Bootstrap components"""
        component = data['_component']

        if component == 'card':
            return BootstrapRenderer._render_card(data)
        elif component == 'button':
            return f'<button class="btn btn-{data.get("variant", "primary")}">{data.get("text", "")}</button>'
        elif component == 'alert':
            return f'<div class="alert alert-{data.get("type", "info")}">{data.get("message", "")}</div>'
        else:
            return f'<div>{data}</div>'

    @staticmethod
    def _render_card(data: Dict) -> str:
        """Render a Bootstrap card"""
        return f"""
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{data.get('title', '')}</h5>
                <p class="card-text">{data.get('text', '')}</p>
            </div>
        </div>
        """

    @staticmethod
    def _render_grid(data: Dict) -> str:
        """Render a Bootstrap grid"""
        cols = ''.join(f'<div class="col">{BootstrapRenderer.render(col)}</div>'
                      for col in data.get('columns', []))
        return f'<div class="row">{cols}</div>'


# ============================================
# Test the different approaches
# ============================================

if __name__ == "__main__":
    # Sample template data
    sample_templates = [
        {
            'id': 'blog/posts',
            'name': 'Blog Posts',
            'category': 'CMS',
            'description': 'Manage blog posts with SEO',
            'fields_count': 8
        },
        {
            'id': 'ecommerce/products',
            'name': 'Products',
            'category': 'E-Commerce',
            'description': 'Product catalog management',
            'fields_count': 12
        }
    ]

    print("Testing different approaches...")
    print("\n1. Functional composition approach:")
    print(render_template_marketplace(sample_templates)[:500] + "...")

    print("\n2. Direct dict structure:")
    test_dict = {
        'type': 'card',
        'title': 'Test Card',
        'text': 'This is a test card'
    }
    print(dict_to_bootstrap(test_dict))

    print("\n3. Pure data transformation:")
    test_data = {
        '_component': 'card',
        'title': 'Test Card',
        'text': 'Using renderer class'
    }
    print(BootstrapRenderer.render(test_data))