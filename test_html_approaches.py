#!/usr/bin/env python3
"""
Test different approaches to see what feels most natural for DBBasic
"""

# ============================================
# APPROACH 1: Pure Python data structures
# ============================================

def approach1_pure_dicts():
    """Everything is just dicts and lists"""

    page = {
        "navbar": {
            "brand": "DBBasic",
            "links": [
                {"text": "Monitor", "url": "http://localhost:8004"},
                {"text": "Data", "url": "http://localhost:8005"}
            ]
        },
        "content": {
            "title": "Template Marketplace",
            "cards": [
                {
                    "title": "Blog Posts",
                    "badge": "CMS",
                    "description": "Manage blog posts with SEO",
                    "actions": [
                        {"type": "button", "text": "Deploy", "variant": "success"},
                        {"type": "button", "text": "Preview", "variant": "secondary"}
                    ]
                }
            ]
        }
    }

    return page


# ============================================
# APPROACH 2: Minimal markup helpers
# ============================================

def approach2_minimal_helpers():
    """Simple helper functions that return dicts"""

    def nav(brand, *links):
        return {"nav": {"brand": brand, "links": links}}

    def card(title, desc, badge=None):
        return {
            "card": {
                "title": title,
                "desc": desc,
                "badge": badge
            }
        }

    def btn(text, action=None, style="primary"):
        return {"btn": text, "action": action, "style": style}

    # Usage
    page = {
        "nav": nav("DBBasic",
                  {"text": "Monitor", "url": "/monitor"},
                  {"text": "Data", "url": "/data"}),
        "cards": [
            card("Blog Posts", "Manage content", badge="CMS"),
            card("Products", "E-commerce catalog", badge="Shop")
        ]
    }

    return page


# ============================================
# APPROACH 3: Component classes
# ============================================

class Component:
    def to_dict(self):
        return self.__dict__

class Card(Component):
    def __init__(self, title, description, badge=None):
        self.type = "card"
        self.title = title
        self.description = description
        self.badge = badge
        self.actions = []

    def add_action(self, text, action):
        self.actions.append({"text": text, "action": action})
        return self

class Page(Component):
    def __init__(self, title):
        self.type = "page"
        self.title = title
        self.components = []

    def add(self, component):
        self.components.append(component.to_dict() if hasattr(component, 'to_dict') else component)
        return self


def approach3_component_classes():
    """OOP-style component building"""

    page = Page("Template Marketplace")

    card = Card("Blog Posts", "Content management", "CMS")
    card.add_action("Deploy", "deploy('blog')")
    card.add_action("Preview", "preview('blog')")

    page.add(card)

    return page.to_dict()


# ============================================
# APPROACH 4: Bootstrap-aware converter
# ============================================

def to_bootstrap(data):
    """Convert Python data structures to Bootstrap HTML

    Rules:
    - Dict with 'card' key -> Bootstrap card
    - Dict with 'nav' key -> Bootstrap navbar
    - List -> Bootstrap grid
    - String -> Raw HTML
    """

    if isinstance(data, dict):
        if 'card' in data:
            c = data['card']
            return f'''
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{c.get('title', '')}</h5>
                    <p class="card-text">{c.get('desc', '')}</p>
                </div>
            </div>'''

        elif 'nav' in data:
            n = data['nav']
            links = ''.join([f'<a class="nav-link" href="{l["url"]}">{l["text"]}</a>'
                           for l in n.get('links', [])])
            return f'''
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
                <a class="navbar-brand" href="#">{n.get('brand', '')}</a>
                <div class="navbar-nav ms-auto">{links}</div>
            </nav>'''

        elif 'grid' in data:
            cols = ''.join([f'<div class="col">{to_bootstrap(item)}</div>'
                          for item in data['grid']])
            return f'<div class="row">{cols}</div>'

    elif isinstance(data, list):
        # Lists become grids by default
        return to_bootstrap({'grid': data})

    return str(data)


# ============================================
# APPROACH 5: YAML-like structure
# ============================================

def approach5_yaml_like():
    """Structure that would work well in YAML"""

    page = {
        "layout": "dashboard",
        "components": [
            {
                "type": "navbar",
                "brand": "DBBasic",
                "links": ["Monitor", "Data", "Templates"]
            },
            {
                "type": "hero",
                "title": "Template Marketplace",
                "subtitle": "Deploy apps instantly"
            },
            {
                "type": "grid",
                "columns": 3,
                "items": [
                    {
                        "type": "card",
                        "title": "Blog",
                        "category": "CMS",
                        "actions": ["deploy", "preview"]
                    }
                ]
            }
        ]
    }

    return page


# ============================================
# Test all approaches
# ============================================

print("=" * 60)
print("APPROACH 1: Pure Python dicts")
print("=" * 60)
result1 = approach1_pure_dicts()
print(result1)

print("\n" + "=" * 60)
print("APPROACH 2: Minimal helpers")
print("=" * 60)
result2 = approach2_minimal_helpers()
print(result2)

print("\n" + "=" * 60)
print("APPROACH 3: Component classes")
print("=" * 60)
result3 = approach3_component_classes()
print(result3)

print("\n" + "=" * 60)
print("APPROACH 4: Bootstrap converter example")
print("=" * 60)
sample = {"card": {"title": "Test Card", "desc": "This is a test"}}
print(to_bootstrap(sample))

print("\n" + "=" * 60)
print("APPROACH 5: YAML-friendly structure")
print("=" * 60)
result5 = approach5_yaml_like()
print(result5)

print("\n" + "=" * 60)
print("Which approach feels most natural for DBBasic?")
print("1. Pure dicts - Simple, no magic")
print("2. Minimal helpers - Slight abstraction")
print("3. Component classes - OOP style")
print("4. Smart converter - Infers HTML from structure")
print("5. YAML-like - Config-driven")