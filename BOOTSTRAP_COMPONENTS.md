# Bootstrap 5.3 Component Library for DBBasic

## 📚 Complete Component Reference

### Layout Components

#### Container
```python
{
    'type': 'container',
    'fluid': False,  # True for container-fluid
    'children': [...]
}
```

#### Row/Column Grid
```python
{
    'type': 'row',
    'children': [
        {'type': 'col', 'size': 6, 'children': [...]},
        {'type': 'col', 'size': 6, 'children': [...]}
    ]
}
```

### Navigation

#### Navbar (Complete)
```python
{
    'type': 'navbar',
    'brand': 'DBBasic',
    'variant': 'light',  # light, dark
    'position': 'fixed-top',  # fixed-top, fixed-bottom, sticky-top
    'links': [...],
    'search': True,  # Include search box
    'user_menu': {...}  # User dropdown
}
```

#### Breadcrumb
```python
{
    'type': 'breadcrumb',
    'items': [
        {'text': 'Home', 'url': '/'},
        {'text': 'Products', 'url': '/products'},
        {'text': 'Item', 'active': True}
    ]
}
```

#### Tabs
```python
{
    'type': 'tabs',
    'items': [
        {'id': 'tab1', 'label': 'Tab 1', 'content': {...}, 'active': True},
        {'id': 'tab2', 'label': 'Tab 2', 'content': {...}}
    ]
}
```

### Content

#### Card (Enhanced)
```python
{
    'type': 'card',
    'title': 'Card Title',
    'subtitle': 'Card subtitle',
    'image': {'src': '/image.jpg', 'position': 'top'},  # top, bottom
    'body': 'Card content or components',
    'list_group': [...],  # List items
    'footer': {...},
    'header': {...}
}
```

#### Accordion
```python
{
    'type': 'accordion',
    'id': 'accordion1',
    'items': [
        {
            'header': 'Section 1',
            'body': 'Content 1',
            'expanded': True
        }
    ]
}
```

#### List Group
```python
{
    'type': 'list_group',
    'flush': True,  # Remove borders
    'items': [
        {'text': 'Item 1', 'active': True},
        {'text': 'Item 2', 'badge': '5'},
        {'text': 'Item 3', 'variant': 'danger'}
    ]
}
```

### Forms

#### Form
```python
{
    'type': 'form',
    'method': 'POST',
    'action': '/submit',
    'fields': [
        {
            'type': 'input',
            'name': 'email',
            'label': 'Email',
            'input_type': 'email',
            'required': True,
            'help': 'We will never share your email'
        },
        {
            'type': 'select',
            'name': 'country',
            'label': 'Country',
            'options': [
                {'value': 'us', 'text': 'United States'},
                {'value': 'uk', 'text': 'United Kingdom'}
            ]
        },
        {
            'type': 'textarea',
            'name': 'message',
            'label': 'Message',
            'rows': 4
        },
        {
            'type': 'checkbox',
            'name': 'agree',
            'label': 'I agree to terms'
        },
        {
            'type': 'radio_group',
            'name': 'plan',
            'label': 'Select Plan',
            'options': [
                {'value': 'free', 'text': 'Free'},
                {'value': 'pro', 'text': 'Pro'}
            ]
        }
    ],
    'buttons': [
        {'type': 'submit', 'text': 'Submit', 'variant': 'primary'},
        {'type': 'reset', 'text': 'Clear', 'variant': 'secondary'}
    ]
}
```

#### Input Group
```python
{
    'type': 'input_group',
    'prepend': '@',  # Text or component
    'input': {'type': 'input', 'name': 'username'},
    'append': {'type': 'button', 'text': 'Go'}
}
```

### Data Display

#### Table
```python
{
    'type': 'table',
    'striped': True,
    'hover': True,
    'bordered': False,
    'responsive': True,
    'headers': ['Name', 'Email', 'Role'],
    'rows': [
        ['John Doe', 'john@example.com', 'Admin'],
        ['Jane Smith', 'jane@example.com', 'User']
    ],
    'footer': [...]  # Optional footer
}
```

#### Badge
```python
{
    'type': 'badge',
    'text': 'New',
    'variant': 'primary',  # primary, secondary, success, etc.
    'pill': True  # Rounded badge
}
```

#### Progress
```python
{
    'type': 'progress',
    'value': 75,
    'min': 0,
    'max': 100,
    'label': '75%',
    'variant': 'success',
    'striped': True,
    'animated': True
}
```

### Feedback

#### Alert (Enhanced)
```python
{
    'type': 'alert',
    'message': 'Alert message',
    'variant': 'warning',
    'dismissible': True,
    'icon': 'exclamation-triangle',  # Bootstrap icon
    'heading': 'Warning!'
}
```

#### Toast
```python
{
    'type': 'toast',
    'title': 'Notification',
    'message': 'Your data has been saved',
    'time': '2 mins ago',
    'autohide': True,
    'delay': 5000
}
```

#### Modal
```python
{
    'type': 'modal',
    'id': 'modal1',
    'title': 'Modal Title',
    'body': {...},  # Component or text
    'footer': [
        {'type': 'button', 'text': 'Close', 'dismiss': True},
        {'type': 'button', 'text': 'Save', 'variant': 'primary'}
    ],
    'size': 'lg',  # sm, lg, xl
    'centered': True,
    'scrollable': True
}
```

### Components

#### Button (Enhanced)
```python
{
    'type': 'button',
    'text': 'Click me',
    'variant': 'primary',  # primary, secondary, success, danger, warning, info, light, dark
    'size': 'md',  # sm, md, lg
    'outline': False,  # Outline style
    'block': False,  # Full width
    'disabled': False,
    'icon': 'plus',  # Bootstrap icon
    'loading': False,  # Show spinner
    'tooltip': 'Click to submit'
}
```

#### Button Group
```python
{
    'type': 'button_group',
    'size': 'md',
    'vertical': False,
    'buttons': [
        {'text': 'Left', 'variant': 'primary'},
        {'text': 'Middle', 'variant': 'primary'},
        {'text': 'Right', 'variant': 'primary'}
    ]
}
```

#### Dropdown
```python
{
    'type': 'dropdown',
    'text': 'Options',
    'variant': 'secondary',
    'items': [
        {'text': 'Action', 'url': '#'},
        {'divider': True},
        {'text': 'Another action', 'url': '#'}
    ]
}
```

#### Carousel
```python
{
    'type': 'carousel',
    'id': 'carousel1',
    'indicators': True,
    'controls': True,
    'slides': [
        {
            'image': '/slide1.jpg',
            'caption': 'First slide',
            'description': 'Description text'
        }
    ]
}
```

#### Spinner
```python
{
    'type': 'spinner',
    'variant': 'primary',
    'size': 'md',  # sm, md
    'type': 'border'  # border, grow
}
```

#### Pagination
```python
{
    'type': 'pagination',
    'current': 2,
    'total': 10,
    'size': 'md',  # sm, md, lg
    'max_visible': 5
}
```

### Utilities

#### Spacing
```python
{
    'type': 'div',
    'classes': ['mb-3', 'mt-2', 'px-4'],  # Bootstrap utility classes
    'children': [...]
}
```

#### Flex
```python
{
    'type': 'flex',
    'direction': 'row',  # row, column
    'justify': 'between',  # start, center, end, between, around
    'align': 'center',  # start, center, end
    'wrap': True,
    'children': [...]
}
```

## 🎨 Component Composition Example

```python
# Complex page with multiple components
page = {
    'type': 'page',
    'title': 'Dashboard',
    'components': [
        {
            'type': 'navbar',
            'brand': 'DBBasic',
            'links': ['Dashboard', 'Reports', 'Settings']
        },
        {
            'type': 'container',
            'children': [
                {
                    'type': 'breadcrumb',
                    'items': [
                        {'text': 'Home', 'url': '/'},
                        {'text': 'Dashboard', 'active': True}
                    ]
                },
                {
                    'type': 'row',
                    'children': [
                        {
                            'type': 'col',
                            'size': 8,
                            'children': [
                                {
                                    'type': 'card',
                                    'title': 'Sales Overview',
                                    'body': {
                                        'type': 'table',
                                        'headers': ['Product', 'Sales'],
                                        'rows': [['Widget', '$1000']]
                                    }
                                }
                            ]
                        },
                        {
                            'type': 'col',
                            'size': 4,
                            'children': [
                                {
                                    'type': 'card',
                                    'title': 'Quick Stats',
                                    'body': {
                                        'type': 'list_group',
                                        'items': [
                                            {'text': 'Users: 1,234'},
                                            {'text': 'Revenue: $45,678'}
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
```

## 🚀 Implementation Plan

### Phase 1: Core Components ✅
- Page, Container, Grid
- Navbar, Card, Button
- Alert, Hero

### Phase 2: Forms & Tables (Current)
- Complete form controls
- Table with sorting/filtering
- Input groups and validation

### Phase 3: Advanced Components
- Modal, Toast, Popover
- Carousel, Accordion
- Tabs, Pills

### Phase 4: Utilities
- Spacing helpers
- Color themes
- Responsive utilities

## 🔧 Testing with Selenium

```python
from selenium import webdriver
from presentation_layer import PresentationLayer

# Generate test page
ui = {'type': 'page', 'components': [...]}
html = PresentationLayer.render(ui, 'bootstrap')

# Save and test with Selenium
with open('test.html', 'w') as f:
    f.write(html)

driver = webdriver.Chrome()
driver.get('file:///path/to/test.html')

# Verify rendering
assert driver.find_element_by_class_name('navbar')
assert driver.find_element_by_class_name('card')
```

---

This comprehensive component library ensures DBBasic can generate any Bootstrap UI through simple data structures.