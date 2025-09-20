#!/usr/bin/env python3
"""
Tailwind CSS Renderer for Presentation Layer
Provides Tailwind CSS 3.x component rendering
"""

from typing import Dict, List, Any, Optional
from presentation_layer import UIRenderer

class TailwindRenderer(UIRenderer):
    """Tailwind CSS renderer implementation"""

    def render_page(self, data: Dict) -> str:
        """Render a complete page with Tailwind CSS"""
        title = data.get('title', 'DBBasic')
        components = data.get('components', [])

        # Render all components
        body_content = ''.join([self.render(comp) for comp in components])

        return f'''<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="h-full bg-gray-50">
    {body_content}
</body>
</html>'''

    def render_navbar(self, data: Dict) -> str:
        """Render Tailwind navigation bar"""
        brand = data.get('brand', 'DBBasic')
        links = data.get('links', [])
        variant = data.get('variant', 'light')

        # Tailwind navbar classes
        nav_class = 'bg-white shadow' if variant == 'light' else 'bg-gray-900'
        text_class = 'text-gray-900' if variant == 'light' else 'text-white'
        link_class = 'text-gray-700 hover:text-indigo-600' if variant == 'light' else 'text-gray-300 hover:text-white'

        links_html = ''.join([
            f'<a href="{link.get("url", "#")}" class="{link_class} px-3 py-2 rounded-md text-sm font-medium">{link.get("text", "")}</a>'
            for link in links
        ])

        return f'''
        <nav class="{nav_class}">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex">
                        <div class="flex-shrink-0 flex items-center">
                            <h1 class="{text_class} text-2xl font-bold">{brand}</h1>
                        </div>
                        <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                            {links_html}
                        </div>
                    </div>
                </div>
            </div>
        </nav>
        '''

    def render_hero(self, data: Dict) -> str:
        """Render Tailwind hero section"""
        title = data.get('title', '')
        subtitle = data.get('subtitle', '')
        variant = data.get('variant', 'default')

        # Gradient backgrounds
        bg_class = {
            'default': 'bg-white',
            'gradient-blue': 'bg-gradient-to-r from-blue-600 to-indigo-600',
            'gradient-purple': 'bg-gradient-to-r from-purple-600 to-pink-600',
            'gradient-green': 'bg-gradient-to-r from-green-600 to-teal-600'
        }.get(variant, 'bg-white')

        text_color = 'text-white' if 'gradient' in variant else 'text-gray-900'

        return f'''
        <div class="{bg_class} py-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center">
                    <h1 class="{text_color} text-4xl font-bold sm:text-5xl md:text-6xl">
                        {title}
                    </h1>
                    <p class="{text_color} mt-3 max-w-2xl mx-auto text-xl sm:mt-4">
                        {subtitle}
                    </p>
                </div>
            </div>
        </div>
        '''

    def render_card(self, data: Dict) -> str:
        """Render Tailwind card component"""
        title = data.get('title', '')
        description = data.get('description', '')
        body = data.get('body', '')
        footer = data.get('footer', '')

        # Process body content
        if isinstance(body, dict):
            body_html = self.render(body)
        elif isinstance(body, list):
            body_html = ''.join([self.render(item) for item in body])
        else:
            body_html = str(body)

        # Footer content
        footer_html = ''
        if footer:
            if isinstance(footer, dict):
                footer_html = f'<div class="px-6 py-4 bg-gray-50 border-t">{self.render(footer)}</div>'
            else:
                footer_html = f'<div class="px-6 py-4 bg-gray-50 border-t">{footer}</div>'

        return f'''
        <div class="bg-white overflow-hidden shadow rounded-lg">
            {f'<div class="px-6 py-4 border-b"><h3 class="text-lg font-medium text-gray-900">{title}</h3></div>' if title else ''}
            <div class="px-6 py-4">
                {f'<p class="text-gray-600 mb-4">{description}</p>' if description else ''}
                {body_html}
            </div>
            {footer_html}
        </div>
        '''

    def render_button(self, data: Dict) -> str:
        """Render Tailwind button"""
        text = data.get('text', 'Button')
        variant = data.get('variant', 'primary')
        size = data.get('size', 'md')
        onclick = data.get('onclick', '')

        # Variant styles
        variant_classes = {
            'primary': 'bg-indigo-600 hover:bg-indigo-700 text-white',
            'secondary': 'bg-gray-200 hover:bg-gray-300 text-gray-900',
            'success': 'bg-green-600 hover:bg-green-700 text-white',
            'danger': 'bg-red-600 hover:bg-red-700 text-white',
            'warning': 'bg-yellow-500 hover:bg-yellow-600 text-white',
            'info': 'bg-blue-500 hover:bg-blue-600 text-white'
        }.get(variant, 'bg-gray-200 hover:bg-gray-300 text-gray-900')

        # Size classes
        size_classes = {
            'sm': 'px-3 py-1.5 text-sm',
            'md': 'px-4 py-2 text-base',
            'lg': 'px-6 py-3 text-lg'
        }.get(size, 'px-4 py-2 text-base')

        onclick_attr = f'onclick="{onclick}"' if onclick else ''

        return f'<button class="{variant_classes} {size_classes} font-medium rounded-md shadow-sm" {onclick_attr}>{text}</button>'

    def render_grid(self, data: Dict) -> str:
        """Render Tailwind grid layout"""
        columns = data.get('columns', 3)
        items = data.get('items', [])
        gap = data.get('gap', 4)

        # Grid column classes
        col_class = {
            1: 'grid-cols-1',
            2: 'grid-cols-1 sm:grid-cols-2',
            3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
            4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
            6: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6'
        }.get(columns, 'grid-cols-3')

        items_html = ''.join([f'<div>{self.render(item)}</div>' for item in items])

        return f'''
        <div class="grid {col_class} gap-{gap}">
            {items_html}
        </div>
        '''

    def render_table(self, data: Dict) -> str:
        """Render Tailwind table"""
        headers = data.get('headers', [])
        rows = data.get('rows', [])

        # Create header row
        header_html = ''.join([
            f'<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{header}</th>'
            for header in headers
        ])

        # Create data rows
        rows_html = ''
        for row in rows:
            cells_html = ''.join([
                f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{self.render(cell) if isinstance(cell, dict) else cell}</td>'
                for cell in row
            ])
            rows_html += f'<tr class="hover:bg-gray-50">{cells_html}</tr>'

        return f'''
        <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table class="min-w-full divide-y divide-gray-300">
                <thead class="bg-gray-50">
                    <tr>{header_html}</tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {rows_html}
                </tbody>
            </table>
        </div>
        '''

    def render_form(self, data: Dict) -> str:
        """Render Tailwind form"""
        fields = data.get('fields', [])
        submit = data.get('submit', {})
        form_id = data.get('id', '')

        fields_html = ''
        for field in fields:
            field_html = self.render_form_field(field)
            fields_html += f'<div class="mb-4">{field_html}</div>'

        submit_html = ''
        if submit:
            submit_button = {
                'type': 'button',
                'text': submit.get('text', 'Submit'),
                'variant': submit.get('variant', 'primary')
            }
            submit_html = self.render_button(submit_button)

        return f'''
        <form {f'id="{form_id}"' if form_id else ''} class="space-y-6">
            {fields_html}
            <div class="flex justify-end">
                {submit_html}
            </div>
        </form>
        '''

    def render_form_field(self, field: Dict) -> str:
        """Render individual form field"""
        field_type = field.get('type', 'input')
        label = field.get('label', '')
        name = field.get('name', '')
        field_id = field.get('id', name)
        placeholder = field.get('placeholder', '')
        required = field.get('required', False)

        label_html = f'<label for="{field_id}" class="block text-sm font-medium text-gray-700 mb-1">{label}</label>' if label else ''

        if field_type == 'input':
            input_type = field.get('input_type', 'text')
            return f'''
            {label_html}
            <input type="{input_type}" id="{field_id}" name="{name}"
                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                   placeholder="{placeholder}" {'required' if required else ''}>
            '''
        elif field_type == 'textarea':
            rows = field.get('rows', 4)
            return f'''
            {label_html}
            <textarea id="{field_id}" name="{name}" rows="{rows}"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="{placeholder}" {'required' if required else ''}></textarea>
            '''
        elif field_type == 'select':
            options = field.get('options', [])
            options_html = ''.join([
                f'<option value="{opt.get("value", "")}">{opt.get("text", "")}</option>'
                for opt in options
            ])
            return f'''
            {label_html}
            <select id="{field_id}" name="{name}"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                {options_html}
            </select>
            '''
        elif field_type == 'checkbox':
            return f'''
            <div class="flex items-center">
                <input type="checkbox" id="{field_id}" name="{name}"
                       class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                <label for="{field_id}" class="ml-2 block text-sm text-gray-900">{label}</label>
            </div>
            '''

        return ''

    def render_badge(self, data: Dict) -> str:
        """Render Tailwind badge"""
        text = data.get('text', '')
        variant = data.get('variant', 'default')

        variant_classes = {
            'default': 'bg-gray-100 text-gray-800',
            'primary': 'bg-blue-100 text-blue-800',
            'success': 'bg-green-100 text-green-800',
            'danger': 'bg-red-100 text-red-800',
            'warning': 'bg-yellow-100 text-yellow-800',
            'info': 'bg-indigo-100 text-indigo-800'
        }.get(variant, 'bg-gray-100 text-gray-800')

        return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {variant_classes}">{text}</span>'

    def render_alert(self, data: Dict) -> str:
        """Render Tailwind alert"""
        message = data.get('message', '')
        variant = data.get('variant', 'info')

        variant_classes = {
            'info': 'bg-blue-50 border-blue-400 text-blue-700',
            'success': 'bg-green-50 border-green-400 text-green-700',
            'warning': 'bg-yellow-50 border-yellow-400 text-yellow-700',
            'danger': 'bg-red-50 border-red-400 text-red-700'
        }.get(variant, 'bg-blue-50 border-blue-400 text-blue-700')

        return f'''
        <div class="{variant_classes} border-l-4 p-4" role="alert">
            <p>{message}</p>
        </div>
        '''

    def render_metric(self, data: Dict) -> str:
        """Render metric display component"""
        label = data.get('label', '')
        value = data.get('value', '0')
        icon = data.get('icon', '')
        trend = data.get('trend', '')

        icon_html = f'<i class="{icon} text-3xl text-indigo-600"></i>' if icon else ''

        trend_html = ''
        if trend == 'up':
            trend_html = '<span class="text-green-600">↑</span>'
        elif trend == 'down':
            trend_html = '<span class="text-red-600">↓</span>'

        return f'''
        <div class="flex items-center justify-between p-4">
            {icon_html}
            <div class="text-right">
                <p class="text-2xl font-bold text-gray-900">{value} {trend_html}</p>
                <p class="text-sm text-gray-500">{label}</p>
            </div>
        </div>
        '''

    def render_container(self, data: Dict) -> str:
        """Render Tailwind container"""
        children = data.get('children', [])
        fluid = data.get('fluid', False)

        container_class = 'max-w-full' if fluid else 'max-w-7xl'

        children_html = ''.join([self.render(child) for child in children])

        return f'''
        <div class="{container_class} mx-auto px-4 sm:px-6 lg:px-8">
            {children_html}
        </div>
        '''

    def render(self, data: Any) -> str:
        """Main render method"""
        if isinstance(data, str):
            return data

        if isinstance(data, list):
            return ''.join([self.render(item) for item in data])

        if isinstance(data, dict):
            component_type = data.get('type', '')

            # Map component types to render methods
            renderers = {
                'page': self.render_page,
                'navbar': self.render_navbar,
                'hero': self.render_hero,
                'card': self.render_card,
                'button': self.render_button,
                'grid': self.render_grid,
                'table': self.render_table,
                'form': self.render_form,
                'badge': self.render_badge,
                'alert': self.render_alert,
                'metric': self.render_metric,
                'container': self.render_container
            }

            renderer = renderers.get(component_type)
            if renderer:
                return renderer(data)

        return str(data)


# Example usage
if __name__ == "__main__":
    from presentation_layer import PresentationLayer

    # Register Tailwind renderer
    PresentationLayer.add_renderer('tailwind', TailwindRenderer())

    # Example data structure
    ui_data = {
        'type': 'page',
        'title': 'DBBasic - Tailwind Version',
        'components': [
            {
                'type': 'navbar',
                'brand': 'DBBasic',
                'variant': 'dark',
                'links': [
                    {'text': 'Dashboard', 'url': '/'},
                    {'text': 'Services', 'url': '/services'},
                    {'text': 'Templates', 'url': '/templates'}
                ]
            },
            {
                'type': 'hero',
                'title': 'Welcome to DBBasic',
                'subtitle': 'The Post-Code Era Platform',
                'variant': 'gradient-blue'
            },
            {
                'type': 'container',
                'children': [
                    {
                        'type': 'grid',
                        'columns': 3,
                        'items': [
                            {
                                'type': 'card',
                                'title': 'Fast Performance',
                                'body': {
                                    'type': 'metric',
                                    'label': 'Queries/sec',
                                    'value': '402M',
                                    'icon': 'fas fa-rocket',
                                    'trend': 'up'
                                }
                            },
                            {
                                'type': 'card',
                                'title': 'AI Powered',
                                'body': 'Generate business logic from natural language'
                            },
                            {
                                'type': 'card',
                                'title': 'Config Driven',
                                'body': 'Define apps with YAML, not code'
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Render with Tailwind
    html = PresentationLayer.render(ui_data, 'tailwind')

    # Save to file
    with open('static/tailwind_demo.html', 'w') as f:
        f.write(html)

    print("✅ Generated Tailwind demo at static/tailwind_demo.html")
    print("\nYou can now switch between frameworks:")
    print("  Bootstrap: PresentationLayer.render(data, 'bootstrap')")
    print("  Tailwind:  PresentationLayer.render(data, 'tailwind')")