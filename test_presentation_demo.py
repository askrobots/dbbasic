#!/usr/bin/env python3
"""
Demo: Same data structure, multiple UI frameworks
Shows how DBBasic's presentation layer works
"""

from presentation_layer import PresentationLayer

# Define a simple UI structure as pure data
demo_ui = {
    'type': 'page',
    'title': 'DBBasic Demo - Same Data, Different Frameworks',
    'components': [
        {
            'type': 'navbar',
            'brand': 'DBBasic Demo',
            'links': ['Dashboard', 'Data', 'Settings']
        },
        {
            'type': 'alert',
            'message': 'This page demonstrates how the same data structure renders in different UI frameworks',
            'variant': 'info'
        },
        {
            'type': 'hero',
            'title': '🎨 Framework Flexibility',
            'subtitle': 'One data structure, infinite possibilities'
        },
        {
            'type': 'grid',
            'columns': 2,
            'items': [
                {
                    'type': 'card',
                    'title': 'Bootstrap Version',
                    'category': 'Framework',
                    'description': 'Uses Bootstrap 5.3 classes and components',
                    'actions': ['deploy', 'preview']
                },
                {
                    'type': 'card',
                    'title': 'Tailwind Version',
                    'category': 'Framework',
                    'description': 'Uses Tailwind utility classes',
                    'actions': ['deploy', 'preview']
                }
            ]
        },
        {
            'type': 'container',
            'children': [
                '<hr class="my-5">',
                '<h2 class="text-center">Benefits of This Approach</h2>',
                {
                    'type': 'grid',
                    'columns': 3,
                    'items': [
                        {
                            'type': 'card',
                            'title': '🤖 AI-Friendly',
                            'description': 'AI can generate UI by creating data structures'
                        },
                        {
                            'type': 'card',
                            'title': '🎨 Customizable',
                            'description': 'Users can add their own UI framework renderers'
                        },
                        {
                            'type': 'card',
                            'title': '🧹 Clean Code',
                            'description': 'No HTML mixed with Python business logic'
                        }
                    ]
                }
            ]
        }
    ]
}

# Render to Bootstrap
print("Generating Bootstrap version...")
bootstrap_html = PresentationLayer.render(demo_ui, 'bootstrap')
with open('demo_bootstrap.html', 'w') as f:
    f.write(bootstrap_html)
print("✅ Created demo_bootstrap.html")

# Render to Tailwind
print("\nGenerating Tailwind version...")
tailwind_html = PresentationLayer.render(demo_ui, 'tailwind')
with open('demo_tailwind.html', 'w') as f:
    f.write(tailwind_html)
print("✅ Created demo_tailwind.html")

print("\n" + "="*60)
print("SAME DATA STRUCTURE:")
print("="*60)
import json
print(json.dumps(demo_ui, indent=2)[:500] + "...")

print("\n" + "="*60)
print("RENDERS TO DIFFERENT FRAMEWORKS!")
print("="*60)
print("Open demo_bootstrap.html and demo_tailwind.html to compare")