# DBBasic Presentation Layer Data Structure Guide

## Core Philosophy

**Keep structures as clean as possible.** Only add complexity when absolutely necessary.

## The 80/20 Rule

80% of UI needs can be met with simple structures:
```python
{'type': 'card', 'title': 'Hello', 'description': 'World'}
```

The remaining 20% might need IDs or handlers:
```python
{'type': 'card', 'id': 'userCard', 'title': 'User', 'onclick': 'editUser()'}
```

## Structure Levels

### Level 1: Pure Structure (Preferred)
```python
# BEST - Just describe what it is
{
    'type': 'card',
    'title': 'Sales Report',
    'description': 'Q4 2024 Performance'
}
```

### Level 2: Semantic IDs (When Needed)
```python
# GOOD - Add IDs only for JavaScript targeting
{
    'type': 'card',
    'id': 'sales-metric',  # Semantic ID
    'title': 'Sales',
    'body': {'type': 'span', 'id': 'sales-value', 'text': '0'}
}
```

### Level 3: Behavior Hints (Sparingly)
```python
# OK - When behavior is integral to the component
{
    'type': 'button',
    'text': 'Save',
    'action': 'save',  # Semantic action, not JS code
    'variant': 'primary'
}
```

### Level 4: Direct Handlers (Avoid)
```python
# AVOID - Only when absolutely necessary
{
    'type': 'button',
    'text': 'Custom',
    'onclick': 'complexHandler(event, this)'  # Last resort
}
```

## Best Practices

### 1. Use Semantic Names, Not Implementation Details

❌ **Bad:**
```python
{
    'type': 'div',
    'class': 'col-md-6 px-3 mt-2',
    'id': 'div1'
}
```

✅ **Good:**
```python
{
    'type': 'column',
    'size': 'half',
    'id': 'user-profile',
    'spacing': 'normal'
}
```

### 2. Separate Structure from Behavior

❌ **Bad - Mixed concerns:**
```python
{
    'type': 'card',
    'title': 'User',
    'onclick': 'fetch("/api/user").then(r => r.json()).then(updateCard)',
    'style': 'border: 2px solid red; padding: 20px;'
}
```

✅ **Good - Separated:**
```python
# Structure
{
    'type': 'card',
    'id': 'user-card',
    'title': 'User',
    'variant': 'highlight'  # Semantic variant
}

# Behavior (in separate script)
# JavaScript handles the interaction
```

### 3. Use Components, Not Elements

❌ **Bad - Too low-level:**
```python
{
    'type': 'div',
    'children': [
        {'type': 'h5', 'text': 'Title'},
        {'type': 'p', 'text': 'Description'},
        {'type': 'button', 'text': 'Click'}
    ]
}
```

✅ **Good - Semantic component:**
```python
{
    'type': 'card',
    'title': 'Title',
    'description': 'Description',
    'actions': ['click']
}
```

### 4. Data Attributes for Metadata

When you need to attach data:
```python
{
    'type': 'card',
    'id': 'product-card',
    'data': {
        'product-id': '12345',
        'category': 'electronics',
        'price': '99.99'
    },
    'title': 'Laptop'
}
```

This generates:
```html
<div class="card" id="product-card" data-product-id="12345" data-category="electronics" data-price="99.99">
```

### 5. Component Patterns

#### Interactive Component
```python
{
    'type': 'metric',
    'id': 'revenue-metric',  # For updates
    'label': 'Revenue',
    'value': '$0',
    'trend': 'up'
}
```

#### Form Field
```python
{
    'type': 'field',
    'id': 'email-field',  # For form processing
    'name': 'email',
    'label': 'Email Address',
    'validation': 'email',  # Semantic validation
    'required': True
}
```

#### Dynamic List
```python
{
    'type': 'list',
    'id': 'todo-list',  # For adding/removing items
    'items': [
        {'id': 'todo-1', 'text': 'Task 1', 'done': False},
        {'id': 'todo-2', 'text': 'Task 2', 'done': True}
    ]
}
```

## ID Strategy

### When to Use IDs

✅ **Use IDs for:**
- JavaScript targeting (`document.getElementById`)
- WebSocket updates (updating specific elements)
- Form processing (getting form values)
- Analytics tracking

❌ **Don't use IDs for:**
- Styling (use semantic variants)
- Layout (use grid/column components)
- Static content

### ID Naming Convention

```python
# Pattern: {context}-{element}-{purpose}
'user-card-container'
'metrics-revenue-value'
'form-email-input'
'nav-main-menu'
```

## Real-World Examples

### Dashboard with Updates
```python
dashboard = {
    'type': 'page',
    'components': [
        {
            'type': 'metrics_row',
            'children': [
                {
                    'type': 'metric',
                    'id': 'users-total',  # Will be updated via WebSocket
                    'label': 'Total Users',
                    'value': '0'
                },
                {
                    'type': 'metric',
                    'id': 'revenue-total',  # Will be updated via WebSocket
                    'label': 'Revenue',
                    'value': '$0'
                }
            ]
        },
        {
            'type': 'chart',
            'id': 'sales-chart',  # Chart library will target this
            'title': 'Sales Trend'
        }
    ]
}
```

### Form with Validation
```python
form = {
    'type': 'form',
    'id': 'user-form',  # Form submission handler
    'fields': [
        {
            'type': 'input',
            'id': 'name-input',  # For getValue()
            'name': 'name',
            'label': 'Full Name',
            'required': True
        },
        {
            'type': 'input',
            'id': 'email-input',  # For validation
            'name': 'email',
            'label': 'Email',
            'validation': 'email'
        }
    ],
    'submit': 'handleUserForm'  # Semantic action
}
```

## Advanced Patterns

### Component Factory
```python
def create_metric(name: str, label: str, initial_value='0'):
    """Factory for consistent metric components"""
    return {
        'type': 'metric',
        'id': f'metric-{name}',
        'data': {'metric-type': name},
        'label': label,
        'value': initial_value
    }

# Usage
metrics = [
    create_metric('users', 'Active Users'),
    create_metric('revenue', 'Monthly Revenue', '$0'),
    create_metric('orders', 'Orders Today')
]
```

### Reactive Components
```python
# Define component with update channel
{
    'type': 'live_metric',
    'id': 'stock-price',
    'channel': 'stocks/AAPL',  # WebSocket channel
    'label': 'AAPL',
    'value': '$0.00'
}
```

## Migration Strategy

When converting existing HTML to data structures:

### Step 1: Identify Components
```html
<!-- Old -->
<div class="card" id="userCard">
    <h5>User Profile</h5>
    <p>John Doe</p>
    <button onclick="editUser()">Edit</button>
</div>
```

### Step 2: Extract Structure
```python
# New - Focus on what it IS, not how it looks
{
    'type': 'card',
    'id': 'user-card',  # Keep ID if needed for JS
    'title': 'User Profile',
    'content': 'John Doe',
    'actions': [{
        'type': 'button',
        'text': 'Edit',
        'action': 'edit-user'  # Semantic action
    }]
}
```

### Step 3: Move Behavior to Scripts
```javascript
// Separate JavaScript file
document.addEventListener('DOMContentLoaded', () => {
    // Find semantic actions
    document.querySelectorAll('[data-action="edit-user"]').forEach(btn => {
        btn.addEventListener('click', editUser);
    });
});
```

## Guidelines Summary

1. **Start simple** - Add complexity only when needed
2. **Semantic over specific** - 'metric' not 'div with number'
3. **IDs for interaction** - Only when JavaScript needs to find it
4. **Data attributes for metadata** - Keep data with elements
5. **Separate concerns** - Structure ≠ Style ≠ Behavior
6. **Component thinking** - High-level components, not HTML elements
7. **Patterns for consistency** - Reuse patterns across the app

## The Goal

Clean data structures that:
- Are easy to read and understand
- Generate any UI framework
- Support real-world interactivity
- Keep complexity where it belongs
- Make the entire system smoother

Remember: **The best data structure is the simplest one that works.**