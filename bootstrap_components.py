#!/usr/bin/env python3
"""
Extended Bootstrap Components for Presentation Layer
Implements forms, tables, modals, and other advanced components
"""

from typing import Dict, List, Any, Optional
from presentation_layer import UIRenderer, BootstrapRenderer

class ExtendedBootstrapRenderer(BootstrapRenderer):
    """Extended Bootstrap renderer with complete component library"""

    def __init__(self):
        super().__init__()  # Initialize parent class with scripts array

    def render_form(self, data: Dict) -> str:
        """Render a complete Bootstrap form"""
        method = data.get('method', 'POST')
        action = data.get('action', '#')
        form_id = data.get('id', '')
        fields = data.get('fields', [])
        buttons = data.get('buttons', [])
        submit = data.get('submit', None)

        fields_html = []
        for field in fields:
            field_type = field.get('type', 'input')

            if field_type == 'input':
                fields_html.append(self._render_input_field(field))
            elif field_type == 'select':
                fields_html.append(self._render_select_field(field))
            elif field_type == 'textarea':
                fields_html.append(self._render_textarea_field(field))
            elif field_type == 'checkbox':
                fields_html.append(self._render_checkbox_field(field))
            elif field_type == 'radio_group':
                fields_html.append(self._render_radio_group(field))

        # Handle submit button
        buttons_html = ''
        if submit:
            icon = f'<i class="{submit.get("icon", "")} me-2"></i>' if submit.get('icon') else ''
            submit_btn = f'''<button type="submit" class="btn btn-{submit.get('variant', 'primary')}">
                {icon}{submit.get('text', 'Submit')}
            </button>'''
            buttons_html = submit_btn
        elif buttons:
            buttons_html = ' '.join([self.render_button(btn) for btn in buttons])

        id_attr = f'id="{form_id}"' if form_id else ''

        return f"""
        <form method="{method}" action="{action}" {id_attr}>
            {''.join(fields_html)}
            <div class="mt-3">
                {buttons_html}
            </div>
        </form>
        """

    def _render_input_field(self, field: Dict) -> str:
        """Render an input field with Bootstrap styling"""
        name = field.get('name', '')
        label = field.get('label', '')
        input_type = field.get('input_type', 'text')
        placeholder = field.get('placeholder', '')
        required = 'required' if field.get('required', False) else ''
        help_text = field.get('help', '')
        value = field.get('value', '')

        help_html = f'<small class="form-text text-muted">{help_text}</small>' if help_text else ''

        return f"""
        <div class="mb-3">
            <label for="{name}" class="form-label">{label}</label>
            <input type="{input_type}" class="form-control" id="{name}" name="{name}"
                   placeholder="{placeholder}" value="{value}" {required}>
            {help_html}
        </div>
        """

    def _render_select_field(self, field: Dict) -> str:
        """Render a select dropdown"""
        name = field.get('name', '')
        label = field.get('label', '')
        options = field.get('options', [])
        required = 'required' if field.get('required', False) else ''

        options_html = []
        for option in options:
            value = option.get('value', '')
            text = option.get('text', '')
            selected = 'selected' if option.get('selected', False) else ''
            options_html.append(f'<option value="{value}" {selected}>{text}</option>')

        return f"""
        <div class="mb-3">
            <label for="{name}" class="form-label">{label}</label>
            <select class="form-select" id="{name}" name="{name}" {required}>
                <option value="">Choose...</option>
                {''.join(options_html)}
            </select>
        </div>
        """

    def _render_textarea_field(self, field: Dict) -> str:
        """Render a textarea"""
        name = field.get('name', '')
        label = field.get('label', '')
        rows = field.get('rows', 3)
        placeholder = field.get('placeholder', '')
        required = 'required' if field.get('required', False) else ''
        value = field.get('value', '')

        return f"""
        <div class="mb-3">
            <label for="{name}" class="form-label">{label}</label>
            <textarea class="form-control" id="{name}" name="{name}" rows="{rows}"
                      placeholder="{placeholder}" {required}>{value}</textarea>
        </div>
        """

    def _render_checkbox_field(self, field: Dict) -> str:
        """Render a checkbox"""
        name = field.get('name', '')
        label = field.get('label', '')
        checked = 'checked' if field.get('checked', False) else ''

        return f"""
        <div class="form-check mb-3">
            <input class="form-check-input" type="checkbox" id="{name}" name="{name}" {checked}>
            <label class="form-check-label" for="{name}">
                {label}
            </label>
        </div>
        """

    def _render_radio_group(self, field: Dict) -> str:
        """Render a group of radio buttons"""
        name = field.get('name', '')
        label = field.get('label', '')
        options = field.get('options', [])

        radios_html = []
        for i, option in enumerate(options):
            value = option.get('value', '')
            text = option.get('text', '')
            checked = 'checked' if option.get('checked', False) else ''
            radio_id = f"{name}_{i}"

            radios_html.append(f"""
            <div class="form-check">
                <input class="form-check-input" type="radio" name="{name}" id="{radio_id}"
                       value="{value}" {checked}>
                <label class="form-check-label" for="{radio_id}">
                    {text}
                </label>
            </div>
            """)

        return f"""
        <div class="mb-3">
            <label class="form-label">{label}</label>
            {''.join(radios_html)}
        </div>
        """

    def render_table(self, data: Dict) -> str:
        """Render a Bootstrap table"""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        table_id = data.get('id', '')
        striped = 'table-striped' if data.get('striped', True) else ''
        hover = 'table-hover' if data.get('hover', True) else ''
        bordered = 'table-bordered' if data.get('bordered', False) else ''
        responsive = data.get('responsive', True)

        # Build header
        header_html = ''.join([f'<th scope="col">{h}</th>' for h in headers])

        # Build rows
        rows_html = []
        for row in rows:
            cells_html = []
            for cell in row:
                # Check if cell is a component (dict with 'type' key)
                if isinstance(cell, dict) and 'type' in cell:
                    cell_content = self.render(cell)
                else:
                    cell_content = str(cell)
                cells_html.append(f'<td>{cell_content}</td>')
            rows_html.append(f'<tr>{"".join(cells_html)}</tr>')

        id_attr = f'id="{table_id}"' if table_id else ''
        table_html = f"""
        <table class="table {striped} {hover} {bordered}" {id_attr}>
            <thead>
                <tr>{header_html}</tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
        """

        if responsive:
            return f'<div class="table-responsive">{table_html}</div>'
        return table_html

    def render_modal(self, data: Dict) -> str:
        """Render a Bootstrap modal"""
        modal_id = data.get('id', 'modal')
        title = data.get('title', '')
        body = self.render(data.get('body', ''))
        footer = data.get('footer', [])
        size = f'modal-{data.get("size", "")}' if data.get('size') else ''
        centered = 'modal-dialog-centered' if data.get('centered', False) else ''
        scrollable = 'modal-dialog-scrollable' if data.get('scrollable', False) else ''

        footer_html = []
        for btn in footer:
            if btn.get('dismiss'):
                footer_html.append(f'<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{btn.get("text", "Close")}</button>')
            else:
                footer_html.append(self.render_button(btn))

        return f"""
        <div class="modal fade" id="{modal_id}" tabindex="-1">
            <div class="modal-dialog {size} {centered} {scrollable}">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">{title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        {body}
                    </div>
                    <div class="modal-footer">
                        {' '.join(footer_html)}
                    </div>
                </div>
            </div>
        </div>
        """

    def render_breadcrumb(self, data: Dict) -> str:
        """Render a breadcrumb navigation"""
        items = data.get('items', [])

        items_html = []
        for item in items:
            if item.get('active'):
                items_html.append(f'<li class="breadcrumb-item active">{item.get("text", "")}</li>')
            else:
                items_html.append(f'<li class="breadcrumb-item"><a href="{item.get("url", "#")}">{item.get("text", "")}</a></li>')

        return f"""
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                {''.join(items_html)}
            </ol>
        </nav>
        """

    def render_tabs(self, data: Dict) -> str:
        """Render Bootstrap tabs"""
        items = data.get('items', [])

        nav_items = []
        tab_panes = []

        for i, item in enumerate(items):
            tab_id = item.get('id', f'tab-{i}')
            label = item.get('label', f'Tab {i+1}')
            content = self.render(item.get('content', ''))
            active = 'active' if item.get('active', False) else ''

            nav_items.append(f"""
            <li class="nav-item">
                <button class="nav-link {active}" data-bs-toggle="tab" data-bs-target="#{tab_id}">
                    {label}
                </button>
            </li>
            """)

            tab_panes.append(f"""
            <div class="tab-pane fade {'show active' if active else ''}" id="{tab_id}">
                {content}
            </div>
            """)

        return f"""
        <ul class="nav nav-tabs" role="tablist">
            {''.join(nav_items)}
        </ul>
        <div class="tab-content mt-3">
            {''.join(tab_panes)}
        </div>
        """

    def render_accordion(self, data: Dict) -> str:
        """Render Bootstrap accordion"""
        accordion_id = data.get('id', 'accordion')
        items = data.get('items', [])

        items_html = []
        for i, item in enumerate(items):
            item_id = f'{accordion_id}-item-{i}'
            header = item.get('header', '')
            body = self.render(item.get('body', ''))
            expanded = item.get('expanded', False)

            items_html.append(f"""
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button {'collapsed' if not expanded else ''}"
                            type="button" data-bs-toggle="collapse"
                            data-bs-target="#{item_id}">
                        {header}
                    </button>
                </h2>
                <div id="{item_id}" class="accordion-collapse collapse {'show' if expanded else ''}"
                     data-bs-parent="#{accordion_id}">
                    <div class="accordion-body">
                        {body}
                    </div>
                </div>
            </div>
            """)

        return f"""
        <div class="accordion" id="{accordion_id}">
            {''.join(items_html)}
        </div>
        """

    def render_badge(self, data: Dict) -> str:
        """Render a Bootstrap badge"""
        text = data.get('text', '')
        variant = data.get('variant', 'primary')
        pill = 'rounded-pill' if data.get('pill', False) else ''

        return f'<span class="badge bg-{variant} {pill}">{text}</span>'

    def render_progress(self, data: Dict) -> str:
        """Render a progress bar"""
        value = data.get('value', 0)
        min_val = data.get('min', 0)
        max_val = data.get('max', 100)
        label = data.get('label', '')
        variant = data.get('variant', 'primary')
        striped = 'progress-bar-striped' if data.get('striped', False) else ''
        animated = 'progress-bar-animated' if data.get('animated', False) else ''

        return f"""
        <div class="progress">
            <div class="progress-bar bg-{variant} {striped} {animated}"
                 role="progressbar" style="width: {value}%"
                 aria-valuenow="{value}" aria-valuemin="{min_val}" aria-valuemax="{max_val}">
                {label}
            </div>
        </div>
        """

    def render_spinner(self, data: Dict) -> str:
        """Render a loading spinner"""
        variant = data.get('variant', 'primary')
        size = f'spinner-{data.get("type", "border")}-{data.get("size", "md")}' if data.get('size') != 'md' else ''
        spinner_type = data.get('type', 'border')

        return f"""
        <div class="spinner-{spinner_type} text-{variant} {size}" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        """

    def render_pagination(self, data: Dict) -> str:
        """Render pagination controls"""
        current = data.get('current', 1)
        total = data.get('total', 1)
        size = f'pagination-{data.get("size", "")}' if data.get('size') else ''

        items = []

        # Previous button
        items.append(f"""
        <li class="page-item {'disabled' if current == 1 else ''}">
            <a class="page-link" href="#" data-page="{current-1}">Previous</a>
        </li>
        """)

        # Page numbers
        for i in range(1, min(total + 1, 6)):  # Show max 5 pages
            active = 'active' if i == current else ''
            items.append(f"""
            <li class="page-item {active}">
                <a class="page-link" href="#" data-page="{i}">{i}</a>
            </li>
            """)

        # Next button
        items.append(f"""
        <li class="page-item {'disabled' if current == total else ''}">
            <a class="page-link" href="#" data-page="{current+1}">Next</a>
        </li>
        """)

        return f"""
        <nav aria-label="Page navigation">
            <ul class="pagination {size}">
                {''.join(items)}
            </ul>
        </nav>
        """

    def render_toast(self, data: Dict) -> str:
        """Render a Bootstrap toast notification"""
        title = data.get('title', '')
        message = data.get('message', '')
        time = data.get('time', 'just now')
        autohide = 'data-bs-autohide="true"' if data.get('autohide', True) else 'data-bs-autohide="false"'
        delay = f'data-bs-delay="{data.get("delay", 5000)}"' if data.get('autohide', True) else ''

        return f"""
        <div class="toast" role="alert" {autohide} {delay}>
            <div class="toast-header">
                <strong class="me-auto">{title}</strong>
                <small>{time}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                {message}
            </div>
        </div>
        """

    def render_list_group(self, data: Dict) -> str:
        """Render a list group"""
        items = data.get('items', [])
        flush = 'list-group-flush' if data.get('flush', False) else ''

        items_html = []
        for item in items:
            text = item.get('text', '')
            active = 'active' if item.get('active', False) else ''
            variant = f'list-group-item-{item.get("variant", "")}' if item.get('variant') else ''
            badge = f'<span class="badge bg-primary rounded-pill">{item.get("badge", "")}</span>' if item.get('badge') else ''

            items_html.append(f"""
            <li class="list-group-item {active} {variant} d-flex justify-content-between align-items-center">
                {text}
                {badge}
            </li>
            """)

        return f"""
        <ul class="list-group {flush}">
            {''.join(items_html)}
        </ul>
        """

    def render_container(self, data: Dict) -> str:
        """Render a container with children"""
        fluid = 'container-fluid' if data.get('fluid', False) else 'container'
        children = data.get('children', [])

        children_html = []
        for child in children:
            children_html.append(self.render(child))

        return f'<div class="{fluid}">{"".join(children_html)}</div>'

    def render_div(self, data: Dict) -> str:
        """Render a div element with ID and class support"""
        div_id = data.get('id', '')
        div_class = data.get('class', '')
        content = data.get('content', '')
        children = data.get('children', [])

        # Process content or children
        if children:
            inner_html = ''.join([self.render(child) for child in children])
        else:
            inner_html = content

        id_attr = f'id="{div_id}"' if div_id else ''
        class_attr = f'class="{div_class}"' if div_class else ''

        return f'<div {id_attr} {class_attr}>{inner_html}</div>'

    def render(self, data: Any) -> str:
        """Extended render method with new component types"""
        if isinstance(data, dict):
            component_type = data.get('type', '')

            # Handle new component types
            if component_type == 'div':
                return self.render_div(data)
            elif component_type == 'container':
                return self.render_container(data)
            elif component_type == 'form':
                return self.render_form(data)
            elif component_type == 'table':
                return self.render_table(data)
            elif component_type == 'modal':
                return self.render_modal(data)
            elif component_type == 'breadcrumb':
                return self.render_breadcrumb(data)
            elif component_type == 'tabs':
                return self.render_tabs(data)
            elif component_type == 'accordion':
                return self.render_accordion(data)
            elif component_type == 'badge':
                return self.render_badge(data)
            elif component_type == 'progress':
                return self.render_progress(data)
            elif component_type == 'spinner':
                return self.render_spinner(data)
            elif component_type == 'pagination':
                return self.render_pagination(data)
            elif component_type == 'toast':
                return self.render_toast(data)
            elif component_type == 'list_group':
                return self.render_list_group(data)
            elif component_type == 'metric':
                return self.render_metric(data)
            elif component_type == 'script':
                return self.render_script(data)
            elif component_type == 'row':
                return self.render_row(data)
            elif component_type == 'col':
                return self.render_col(data)
            elif component_type == 'list':
                return self.render_list(data)

        # Fall back to parent implementation
        return super().render(data)

    def render_metric(self, data: Dict) -> str:
        """Render a metric card"""
        metric_id = data.get('id', '')
        label = data.get('label', '')
        value = data.get('value', '0')
        icon = data.get('icon', '')

        icon_html = f'<i class="{icon} fs-3 me-2"></i>' if icon else ''
        id_attr = f'id="{metric_id}"' if metric_id else ''

        return f"""
        <div class="text-center">
            {icon_html}
            <h3 class="mb-0" {id_attr}>{value}</h3>
            <small class="text-muted">{label}</small>
        </div>
        """

    def render_script(self, data: Dict) -> str:
        """Render inline JavaScript"""
        content = data.get('content', '')
        return f"<script>{content}</script>"

    def render_row(self, data: Dict) -> str:
        """Render Bootstrap row"""
        children = data.get('children', [])
        children_html = ''.join(self.render(child) for child in children)
        return f'<div class="row">{children_html}</div>'

    def render_col(self, data: Dict) -> str:
        """Render Bootstrap column"""
        size = data.get('size', 12)
        children = data.get('children', [])
        children_html = ''.join(self.render(child) for child in children)
        return f'<div class="col-md-{size}">{children_html}</div>'

    def render_list(self, data: Dict) -> str:
        """Render a list"""
        items = data.get('items', [])
        list_class = data.get('class', '')
        list_id = data.get('id', '')

        items_html = []
        for item in items:
            if isinstance(item, str):
                items_html.append(f'<li>{item}</li>')
            else:
                items_html.append(f'<li>{self.render(item)}</li>')

        id_attr = f'id="{list_id}"' if list_id else ''
        class_attr = f'class="{list_class}"' if list_class else ''

        return f'<ul {id_attr} {class_attr}>{"".join(items_html)}</ul>'


# Test the extended components
if __name__ == "__main__":
    from presentation_layer import PresentationLayer

    # Register the extended renderer
    PresentationLayer.add_renderer('bootstrap_extended', ExtendedBootstrapRenderer())

    # Test page with forms and tables
    test_ui = {
        'type': 'page',
        'title': 'Extended Bootstrap Components Test',
        'components': [
            {'type': 'navbar', 'brand': 'DBBasic Test', 'links': ['Home', 'Forms', 'Tables']},
            {
                'type': 'container',
                'children': [
                    {'type': 'breadcrumb', 'items': [
                        {'text': 'Home', 'url': '/'},
                        {'text': 'Components', 'url': '/components'},
                        {'text': 'Test', 'active': True}
                    ]},
                    {'type': 'alert', 'message': 'Testing extended Bootstrap components', 'variant': 'info'},
                    {
                        'type': 'tabs',
                        'items': [
                            {
                                'id': 'form-tab',
                                'label': 'Form Example',
                                'active': True,
                                'content': {
                                    'type': 'form',
                                    'fields': [
                                        {
                                            'type': 'input',
                                            'name': 'name',
                                            'label': 'Full Name',
                                            'placeholder': 'Enter your name',
                                            'required': True
                                        },
                                        {
                                            'type': 'input',
                                            'name': 'email',
                                            'label': 'Email',
                                            'input_type': 'email',
                                            'help': 'We will never share your email'
                                        },
                                        {
                                            'type': 'select',
                                            'name': 'role',
                                            'label': 'Role',
                                            'options': [
                                                {'value': 'admin', 'text': 'Administrator'},
                                                {'value': 'user', 'text': 'User'},
                                                {'value': 'guest', 'text': 'Guest'}
                                            ]
                                        },
                                        {
                                            'type': 'textarea',
                                            'name': 'bio',
                                            'label': 'Biography',
                                            'rows': 4,
                                            'placeholder': 'Tell us about yourself'
                                        },
                                        {
                                            'type': 'checkbox',
                                            'name': 'newsletter',
                                            'label': 'Subscribe to newsletter'
                                        }
                                    ],
                                    'buttons': [
                                        {'type': 'submit', 'text': 'Submit', 'variant': 'primary'},
                                        {'type': 'reset', 'text': 'Clear', 'variant': 'secondary'}
                                    ]
                                }
                            },
                            {
                                'id': 'table-tab',
                                'label': 'Table Example',
                                'content': {
                                    'type': 'table',
                                    'striped': True,
                                    'hover': True,
                                    'headers': ['ID', 'Name', 'Email', 'Role', 'Status'],
                                    'rows': [
                                        ['1', 'John Doe', 'john@example.com', 'Admin', {'type': 'badge', 'text': 'Active', 'variant': 'success'}],
                                        ['2', 'Jane Smith', 'jane@example.com', 'User', {'type': 'badge', 'text': 'Active', 'variant': 'success'}],
                                        ['3', 'Bob Johnson', 'bob@example.com', 'Guest', {'type': 'badge', 'text': 'Inactive', 'variant': 'secondary'}]
                                    ]
                                }
                            },
                            {
                                'id': 'misc-tab',
                                'label': 'Other Components',
                                'content': {
                                    'type': 'container',
                                    'children': [
                                        {'type': 'progress', 'value': 75, 'label': '75%', 'variant': 'success', 'striped': True, 'animated': True},
                                        {'type': 'spinner', 'variant': 'primary', 'type': 'border'},
                                        {'type': 'pagination', 'current': 3, 'total': 10},
                                        {
                                            'type': 'accordion',
                                            'id': 'test-accordion',
                                            'items': [
                                                {
                                                    'header': 'Section 1',
                                                    'body': 'Content for section 1',
                                                    'expanded': True
                                                },
                                                {
                                                    'header': 'Section 2',
                                                    'body': 'Content for section 2'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Generate HTML
    html = PresentationLayer.render(test_ui, 'bootstrap_extended')

    # Save to file
    with open('test_extended_components.html', 'w') as f:
        f.write(html)

    print("✅ Generated test_extended_components.html with extended Bootstrap components")