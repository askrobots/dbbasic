#!/usr/bin/env python3
"""
DBBasic Template Engine - Clean, Pythonic HTML Generation
Instead of mixing HTML strings in code, use a component-based approach
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class Component:
    """Base component class for building HTML"""
    tag: str
    attrs: Dict[str, str] = None
    children: List[Any] = None
    text: str = None

    def render(self) -> str:
        attrs = self.attrs or {}
        children = self.children or []

        # Build attributes string
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items()) if attrs else ''

        # Self-closing tags
        if self.tag in ['img', 'input', 'meta', 'link', 'br', 'hr']:
            return f'<{self.tag} {attr_str}/>'

        # Opening tag
        html = f'<{self.tag}'
        if attr_str:
            html += f' {attr_str}'
        html += '>'

        # Content
        if self.text:
            html += self.text
        for child in children:
            if isinstance(child, Component):
                html += child.render()
            else:
                html += str(child)

        # Closing tag
        html += f'</{self.tag}>'
        return html


class Page:
    """Page builder using method chaining"""
    def __init__(self, title: str = "DBBasic"):
        self.title = title
        self.components = []
        self.scripts = []
        self.styles = []

    def add(self, component):
        self.components.append(component)
        return self

    def script(self, content: str):
        self.scripts.append(content)
        return self

    def style(self, content: str):
        self.styles.append(content)
        return self

    def render(self) -> str:
        # Build the complete HTML document
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    {''.join(f'<style>{s}</style>' for s in self.styles)}
</head>
<body>
    {''.join(c.render() if isinstance(c, Component) else str(c) for c in self.components)}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {''.join(f'<script>{s}</script>' for s in self.scripts)}
</body>
</html>"""


# Helper functions for common components
def div(**attrs):
    """Create a div component"""
    children = attrs.pop('children', [])
    text = attrs.pop('text', None)
    classes = attrs.pop('classes', [])
    if classes:
        attrs['class'] = ' '.join(classes) if isinstance(classes, list) else classes
    return Component('div', attrs, children, text)

def nav_bar(brand: str, links: List[Dict[str, str]], active: str = None):
    """Create a Bootstrap navbar"""
    nav_items = []
    for link in links:
        is_active = link.get('name') == active
        nav_items.append(
            Component('li', {'class': 'nav-item'}, [
                Component('a', {
                    'class': f"nav-link {'active' if is_active else ''}",
                    'href': link['url']
                }, text=link['name'])
            ])
        )

    return Component('nav', {'class': 'navbar navbar-expand-lg navbar-light bg-light'}, [
        div(classes=['container-fluid'], children=[
            Component('a', {'class': 'navbar-brand', 'href': '#'}, text=brand),
            Component('ul', {'class': 'navbar-nav ms-auto'}, nav_items)
        ])
    ])

def card(title: str, content: str, footer=None, badge=None):
    """Create a Bootstrap card"""
    header_children = [Component('h5', {'class': 'card-title'}, text=title)]
    if badge:
        header_children.append(Component('span', {'class': f'badge bg-{badge["type"]} ms-2'}, text=badge['text']))

    card_children = [
        div(classes=['card-body'], children=[
            div(classes=['d-flex', 'justify-content-between', 'align-items-start'], children=header_children),
            Component('p', {'class': 'card-text'}, text=content)
        ])
    ]

    if footer:
        card_children.append(
            div(classes=['card-footer', 'bg-transparent'], children=footer)
        )

    return div(classes=['card', 'h-100', 'shadow-sm'], children=card_children)

def button(text: str, onclick: str = None, variant: str = 'primary', icon: str = None):
    """Create a Bootstrap button"""
    attrs = {'class': f'btn btn-{variant}'}
    if onclick:
        attrs['onclick'] = onclick

    children = []
    if icon:
        children.append(Component('i', {'class': f'bi bi-{icon} me-2'}))
    children.append(text)

    return Component('button', attrs, children)

def grid(columns: List[Component], cols_md: int = 3):
    """Create a responsive grid"""
    return div(
        classes=[f'row', 'row-cols-1', f'row-cols-md-{cols_md}', 'g-4'],
        children=[div(classes=['col'], children=[col]) for col in columns]
    )

def alert(message: str, alert_type: str = 'info', dismissible: bool = True):
    """Create a Bootstrap alert"""
    classes = ['alert', f'alert-{alert_type}']
    if dismissible:
        classes.append('alert-dismissible')
        classes.append('fade')
        classes.append('show')

    children = [message]
    if dismissible:
        children.append(
            Component('button', {
                'type': 'button',
                'class': 'btn-close',
                'data-bs-dismiss': 'alert'
            })
        )

    return div(classes=classes, children=children, role='alert')


# Template-specific builders
class TemplateMarketplace:
    """Clean template marketplace builder"""

    @staticmethod
    def build(templates: List[Dict[str, Any]]) -> str:
        page = Page("Template Marketplace - DBBasic")

        # Add navigation
        page.add(nav_bar(
            brand="DBBasic",
            links=[
                {'name': 'Monitor', 'url': 'http://localhost:8004'},
                {'name': 'Data', 'url': 'http://localhost:8005'},
                {'name': 'AI Services', 'url': 'http://localhost:8003'},
                {'name': 'Templates', 'url': '/templates'}
            ],
            active='Templates'
        ))

        # Add header
        page.add(div(classes=['container', 'mt-4'], children=[
            div(classes=['text-center', 'mb-5'], children=[
                Component('h1', {'class': 'display-4'}, children=[
                    Component('i', {'class': 'bi bi-shop text-primary me-3'}),
                    'Template Marketplace'
                ]),
                Component('p', {'class': 'lead text-muted'},
                         text='Deploy production-ready applications instantly')
            ]),
            div(id='alerts')
        ]))

        # Build template cards
        cards = []
        for template in templates:
            cards.append(card(
                title=template['name'],
                content=f"{template['description']} • {template['fields_count']} fields",
                badge={'text': template['category'], 'type': 'primary'},
                footer=[
                    button('Preview', f"previewTemplate('{template['id']}')", 'outline-secondary', 'eye'),
                    button('Deploy', f"deployTemplate('{template['id']}')", 'success', 'rocket-takeoff')
                ]
            ))

        # Add grid of cards
        page.add(div(classes=['container'], children=[
            grid(cards, cols_md=3)
        ]))

        # Add styles
        page.style("""
            .card { transition: transform 0.3s; }
            .card:hover { transform: translateY(-5px); }
            .spin { animation: spin 1s linear infinite; }
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        """)

        # Add scripts
        page.script("""
            async function deployTemplate(templateId) {
                const button = event.target;
                const originalHTML = button.innerHTML;

                try {
                    button.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Deploying...';
                    button.disabled = true;

                    const response = await fetch(`/api/templates/deploy?template_id=${encodeURIComponent(templateId)}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });

                    const result = await response.json();

                    if (response.ok) {
                        button.innerHTML = '<i class="bi bi-check-circle"></i> Deployed!';
                        button.className = 'btn btn-success';
                        showAlert(`Template deployed! <a href="${result.url}" class="alert-link">Open →</a>`, 'success');
                    } else {
                        throw new Error(result.detail || 'Deployment failed');
                    }
                } catch (error) {
                    button.innerHTML = '<i class="bi bi-x-circle"></i> Failed';
                    button.className = 'btn btn-danger';
                    showAlert(`Error: ${error.message}`, 'danger');
                } finally {
                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                        button.className = 'btn btn-success';
                        button.disabled = false;
                    }, 3000);
                }
            }

            async function previewTemplate(templateId) {
                try {
                    const response = await fetch(`/api/templates/preview?template_id=${encodeURIComponent(templateId)}`);
                    const result = await response.json();

                    if (response.ok) {
                        showAlert(`Preview: ${result.fields_count} fields, ${result.hooks_count} hooks`, 'info');
                    }
                } catch (error) {
                    showAlert(`Preview failed: ${error.message}`, 'warning');
                }
            }

            function showAlert(message, type) {
                const container = document.getElementById('alerts');
                const alertEl = document.createElement('div');
                alertEl.className = `alert alert-${type} alert-dismissible fade show`;
                alertEl.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                container.appendChild(alertEl);

                setTimeout(() => {
                    if (alertEl.parentNode) {
                        const bsAlert = new bootstrap.Alert(alertEl);
                        bsAlert.close();
                    }
                }, 5000);
            }
        """)

        return page.render()