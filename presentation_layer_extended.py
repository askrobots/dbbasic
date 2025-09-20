#!/usr/bin/env python3
"""
Extended Presentation Layer - Support for IDs, classes, attributes, and scripts
"""

from typing import Dict, List, Any, Optional
from presentation_layer import UIRenderer

class EnhancedBootstrapRenderer(UIRenderer):
    """Enhanced Bootstrap renderer with ID, class, and attribute support"""

    def _extract_attrs(self, data: Dict) -> tuple:
        """Extract common attributes from data structure"""
        attrs = []

        # Standard attributes
        if 'id' in data:
            attrs.append(f'id="{data["id"]}"')

        # Custom classes (in addition to component defaults)
        custom_classes = []
        if 'class' in data:
            custom_classes.append(data['class'])
        if 'classes' in data:
            if isinstance(data['classes'], list):
                custom_classes.extend(data['classes'])
            else:
                custom_classes.append(data['classes'])

        # Style attribute
        if 'style' in data:
            attrs.append(f'style="{data["style"]}"')

        # Data attributes (data-*)
        if 'data' in data:
            for key, value in data['data'].items():
                attrs.append(f'data-{key}="{value}"')

        # Custom attributes
        if 'attrs' in data:
            for key, value in data['attrs'].items():
                attrs.append(f'{key}="{value}"')

        # Event handlers
        for key in data:
            if key.startswith('on'):  # onclick, onchange, etc.
                attrs.append(f'{key}="{data[key]}"')

        return ' '.join(attrs), ' '.join(custom_classes)

    def render_div(self, data: Dict) -> str:
        """Render a div with full attribute support"""
        attrs, custom_classes = self._extract_attrs(data)

        # Build classes
        classes = []
        if data.get('container'):
            classes.append('container')
        if data.get('fluid'):
            classes.append('container-fluid')
        if custom_classes:
            classes.append(custom_classes)

        class_attr = f'class="{" ".join(classes)}"' if classes else ''

        # Render children
        children = data.get('children', [])
        content = data.get('content', '')

        if children:
            content = ''.join([self.render(child) for child in children])

        return f'<div {class_attr} {attrs}>{content}</div>'

    def render_enhanced_card(self, data: Dict) -> str:
        """Card with ID and custom attributes"""
        attrs, custom_classes = self._extract_attrs(data)

        card_classes = ['card']
        if custom_classes:
            card_classes.append(custom_classes)

        # Card header
        header = ''
        if 'header' in data:
            header_id = data.get('header_id', '')
            header = f'''<div class="card-header" {f'id="{header_id}"' if header_id else ''}>
                {self.render(data['header'])}
            </div>'''

        # Card body
        body_id = data.get('body_id', '')
        body_attrs = f'id="{body_id}"' if body_id else ''

        return f'''
        <div class="{' '.join(card_classes)}" {attrs}>
            {header}
            <div class="card-body" {body_attrs}>
                {f'<h5 class="card-title">{data.get("title", "")}</h5>' if 'title' in data else ''}
                {self.render(data.get('body', data.get('description', '')))}
            </div>
            {f'<div class="card-footer">{self.render(data["footer"])}</div>' if 'footer' in data else ''}
        </div>
        '''

    def render_span(self, data: Dict) -> str:
        """Render a span with attributes"""
        attrs, custom_classes = self._extract_attrs(data)
        classes = custom_classes if custom_classes else ''

        return f'<span class="{classes}" {attrs}>{data.get("text", "")}</span>'

    def render_script(self, data: Dict) -> str:
        """Render inline or external script"""
        if 'src' in data:
            attrs = ' '.join([f'{k}="{v}"' for k, v in data.items() if k != 'type'])
            return f'<script {attrs}></script>'
        else:
            return f'<script>{data.get("content", "")}</script>'

    def render_style(self, data: Dict) -> str:
        """Render inline styles"""
        return f'<style>{data.get("content", "")}</style>'

    def render(self, data: Any) -> str:
        """Enhanced render with new component types"""
        if isinstance(data, dict):
            component_type = data.get('type', '')

            # New enhanced components
            if component_type == 'div':
                return self.render_div(data)
            elif component_type == 'span':
                return self.render_span(data)
            elif component_type == 'script':
                return self.render_script(data)
            elif component_type == 'style':
                return self.render_style(data)
            elif component_type == 'card':
                return self.render_enhanced_card(data)
            # ... other enhanced components

        # Fall back to parent implementation
        return super().render(data)


# Example: Component with IDs and JavaScript
def example_with_ids_and_scripts():
    """Example showing how to use IDs, classes, and scripts"""
    return {
        'type': 'page',
        'title': 'Enhanced Example',
        'components': [
            # Style definition
            {
                'type': 'style',
                'content': '''
                    #myCustomCard { border: 2px solid blue; }
                    .highlight { background-color: yellow; }
                '''
            },

            # Card with ID for JavaScript targeting
            {
                'type': 'card',
                'id': 'myCustomCard',
                'class': 'shadow-lg',
                'data': {'user-id': '123', 'role': 'admin'},
                'title': 'Interactive Card',
                'body': {
                    'type': 'div',
                    'children': [
                        {
                            'type': 'span',
                            'id': 'counter',
                            'class': 'badge bg-primary',
                            'text': '0'
                        },
                        ' clicks',
                        {
                            'type': 'button',
                            'id': 'incrementBtn',
                            'text': 'Click Me',
                            'onclick': 'incrementCounter()'
                        }
                    ]
                }
            },

            # Inline script
            {
                'type': 'script',
                'content': '''
                    let count = 0;
                    function incrementCounter() {
                        count++;
                        document.getElementById('counter').textContent = count;
                        if (count > 5) {
                            document.getElementById('myCustomCard').classList.add('highlight');
                        }
                    }
                '''
            }
        ]
    }


# Better approach: Separate concerns
def structured_component_with_behavior():
    """Better pattern: Structure + Behavior separation"""
    return {
        'type': 'page',
        'components': [
            # Structure (data)
            {
                'type': 'div',
                'id': 'app',
                'children': [
                    {
                        'type': 'div',
                        'id': 'metrics-container',
                        'class': 'row',
                        'children': [
                            {
                                'type': 'div',
                                'class': 'col-md-3',
                                'children': [{
                                    'type': 'card',
                                    'body_id': 'metric-1',
                                    'title': 'Metric 1',
                                    'body': '0'
                                }]
                            }
                        ]
                    }
                ]
            }
        ],

        # Behavior (separate from structure)
        'scripts': [
            {
                'type': 'script',
                'src': '/static/js/dashboard.js'
            },
            {
                'type': 'script',
                'content': 'initDashboard();'
            }
        ],

        # Styling (separate from structure)
        'styles': [
            {
                'type': 'link',
                'rel': 'stylesheet',
                'href': '/static/css/dashboard.css'
            }
        ]
    }


# Advanced: Component registry pattern
class ComponentRegistry:
    """Register reusable components with IDs"""

    components = {}

    @classmethod
    def register(cls, name: str, component: Dict):
        """Register a reusable component"""
        cls.components[name] = component

    @classmethod
    def get(cls, name: str, **overrides) -> Dict:
        """Get component with overrides"""
        component = cls.components.get(name, {}).copy()

        # Apply overrides (like ID, custom classes)
        for key, value in overrides.items():
            if key == 'classes' and 'classes' in component:
                # Merge classes
                existing = component.get('classes', [])
                if not isinstance(existing, list):
                    existing = [existing]
                if not isinstance(value, list):
                    value = [value]
                component['classes'] = existing + value
            else:
                component[key] = value

        return component


# Register common components
ComponentRegistry.register('metric_card', {
    'type': 'card',
    'classes': ['metric-card'],
    'body': {
        'type': 'div',
        'children': [
            {'type': 'h2', 'id': '{{metric_id}}', 'text': '0'},
            {'type': 'small', 'text': '{{metric_label}}'}
        ]
    }
})

# Use registered component with custom ID
def use_registered_components():
    return {
        'type': 'page',
        'components': [
            ComponentRegistry.get('metric_card',
                                 id='revenue-card',
                                 metric_id='revenue-value',
                                 metric_label='Revenue')
        ]
    }


if __name__ == "__main__":
    print("Enhanced Presentation Layer Features:")
    print("\n1. ID Support:")
    print("   {'type': 'div', 'id': 'myDiv'}")

    print("\n2. Custom Classes:")
    print("   {'type': 'card', 'classes': ['shadow-lg', 'my-custom']}")

    print("\n3. Data Attributes:")
    print("   {'type': 'div', 'data': {'user-id': '123', 'role': 'admin'}}")

    print("\n4. Event Handlers:")
    print("   {'type': 'button', 'onclick': 'handleClick()'}")

    print("\n5. Inline Styles:")
    print("   {'type': 'div', 'style': 'background: red; padding: 10px;'}")

    print("\n6. Scripts & Styles:")
    print("   {'type': 'script', 'content': 'console.log(\"Hello\");'}")
    print("   {'type': 'script', 'src': '/static/js/app.js'}")

    print("\n7. Component Registry:")
    print("   Register once, use everywhere with different IDs")

    print("\nBest Practice: Keep structure (HTML) separate from behavior (JS)")
    print("This maintains the clean separation while allowing full control!")