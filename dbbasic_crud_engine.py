#!/usr/bin/env python3
"""
DBBasic CRUD Engine - Config-Driven CRUD Interface Generator

Converts YAML configurations into live, real-time CRUD interfaces
with WebSocket updates, DuckDB performance, and AI Service Builder integration.
"""

import os
import asyncio
import yaml
import json
import logging
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import duckdb

from dbbasic_crud_engine_presentation import get_crud_dashboard, get_template_marketplace
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, UploadFile, File, Header, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import requests
import aiofiles

# Import presentation layer for clean UI generation
from presentation_layer import PresentationLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CRUDConfigHandler(FileSystemEventHandler):
    """Watches for CRUD config file changes and triggers reloads"""

    def __init__(self, crud_engine):
        self.crud_engine = crud_engine

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('_crud.yaml'):
            logger.info(f"🔄 CRUD config changed: {event.src_path}")
            asyncio.create_task(self.crud_engine.reload_config(event.src_path))

class CRUDResource:
    """Represents a single CRUD resource with its configuration"""

    def __init__(self, config_path: str, config: Dict[str, Any]):
        self.config_path = config_path
        self.config = config
        self.resource_name = config['resource']
        self.database_path = config.get('database', f"{self.resource_name}.db")
        self.fields = config['fields']
        self.interface = config.get('interface', {})
        self.hooks = config.get('hooks', {})
        self.permissions = config.get('permissions', {})
        self.api = config.get('api', {})

        # Initialize database connection
        self.db = duckdb.connect(self.database_path)
        self._create_table()

    def _create_table(self):
        """Create database table based on field configuration"""
        fields_sql = []

        for field_name, field_config in self.fields.items():
            field_type = field_config.get('type', 'string')

            # Map field types to SQL types
            sql_type = {
                'primary_key': 'INTEGER PRIMARY KEY',
                'string': f"VARCHAR({field_config.get('max_length', 255)})",
                'email': 'VARCHAR(255)',
                'decimal': 'DECIMAL(10,2)',
                'integer': 'INTEGER',
                'timestamp': 'TIMESTAMP',
                'boolean': 'BOOLEAN',
                'text': 'TEXT',
                'select': 'VARCHAR(50)'
            }.get(field_type, 'VARCHAR(255)')

            # Add constraints
            constraints = []
            if field_config.get('required', False) and field_type != 'primary_key':
                constraints.append('NOT NULL')
            if field_config.get('unique', False):
                constraints.append('UNIQUE')
            if 'default' in field_config:
                default_val = field_config['default']
                if isinstance(default_val, str):
                    constraints.append(f"DEFAULT '{default_val}'")
                else:
                    constraints.append(f"DEFAULT {default_val}")

            constraint_str = ' ' + ' '.join(constraints) if constraints else ''
            fields_sql.append(f"{field_name} {sql_type}{constraint_str}")

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.resource_name} (
            {', '.join(fields_sql)}
        )
        """

        try:
            self.db.execute(create_sql)
            logger.info(f"✅ Table '{self.resource_name}' created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating table '{self.resource_name}': {e}")

    def generate_list_html(self) -> str:
        """Generate HTML for list view"""
        list_display = self.interface.get('list_display', list(self.fields.keys())[:5])
        search_fields = self.interface.get('search_fields', [])
        filters = self.interface.get('filters', [])

        # Generate search form
        search_form = ""
        if search_fields:
            search_inputs = [f'<input type="text" name="search_{field}" placeholder="Search {field}" class="search-input">'
                           for field in search_fields]
            search_form = f"""
            <div class="search-bar">
                <form class="search-form">
                    {' '.join(search_inputs)}
                    <button type="submit" class="search-btn">Search</button>
                </form>
            </div>
            """

        # Generate filter form
        filter_form = ""
        if filters:
            filter_inputs = []
            for filter_field in filters:
                field_config = self.fields.get(filter_field, {})
                if field_config.get('type') == 'select':
                    options = field_config.get('options', [])
                    option_html = ''.join([f'<option value="{opt}">{opt}</option>' for opt in options])
                    filter_inputs.append(f"""
                    <select name="filter_{filter_field}" class="filter-select">
                        <option value="">All {filter_field}</option>
                        {option_html}
                    </select>
                    """)
                else:
                    filter_inputs.append(f'<input type="text" name="filter_{filter_field}" placeholder="Filter {filter_field}" class="filter-input">')

            if filter_inputs:
                filter_form = f"""
                <div class="filter-bar">
                    <form class="filter-form">
                        {' '.join(filter_inputs)}
                        <button type="submit" class="filter-btn">Filter</button>
                    </form>
                </div>
                """

        # Generate table headers
        headers = [f'<th class="sortable" data-field="{field}">{field.replace("_", " ").title()}</th>'
                  for field in list_display]
        headers.append('<th>Actions</th>')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.resource_name.title()} - DBBasic CRUD</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #333; }}
                .add-btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
                .add-btn:hover {{ background: #0056b3; }}
                .search-bar, .filter-bar {{ margin-bottom: 20px; }}
                .search-form, .filter-form {{ display: flex; gap: 10px; flex-wrap: wrap; }}
                .search-input, .filter-input, .filter-select {{ padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                .search-btn, .filter-btn {{ background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }}
                .search-btn:hover, .filter-btn:hover {{ background: #218838; }}
                .table-container {{ overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f8f9fa; font-weight: 600; cursor: pointer; user-select: none; }}
                th:hover {{ background: #e9ecef; }}
                tr:hover {{ background: #f8f9fa; }}
                .actions {{ display: flex; gap: 8px; }}
                .edit-btn, .delete-btn {{ padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }}
                .edit-btn {{ background: #ffc107; color: #212529; }}
                .delete-btn {{ background: #dc3545; color: white; }}
                .edit-btn:hover {{ background: #e0a800; }}
                .delete-btn:hover {{ background: #c82333; }}
                .status {{ font-weight: 500; padding: 4px 8px; border-radius: 12px; font-size: 12px; }}
                .status.active {{ background: #d4edda; color: #155724; }}
                .status.inactive {{ background: #f8d7da; color: #721c24; }}
                .status.pending {{ background: #fff3cd; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">{self.resource_name.title()} Management</div>
                    <button class="add-btn" onclick="createNew()">+ Add {self.resource_name.title()}</button>
                </div>

                {search_form}
                {filter_form}

                <div class="table-container">
                    <table id="dataTable">
                        <thead>
                            <tr>{''.join(headers)}</tr>
                        </thead>
                        <tbody id="tableBody">
                            <!-- Data will be loaded via WebSocket -->
                        </tbody>
                    </table>
                </div>
            </div>

            <script>
                const resourceName = '{self.resource_name}';
                const ws = new WebSocket('ws://localhost:8005/ws/{self.resource_name}');

                ws.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'data_update') {{
                        updateTable(data.records);
                    }}
                }};

                function updateTable(records) {{
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = records.map(record => `
                        <tr>
                            {' '.join([f"<td>${{record.{field} || ''}}</td>" for field in list_display])}
                            <td class="actions">
                                <button class="edit-btn" onclick="editRecord(${{record.id}})">Edit</button>
                                <button class="delete-btn" onclick="deleteRecord(${{record.id}})">Delete</button>
                            </td>
                        </tr>
                    `).join('');
                }}

                function createNew() {{
                    window.location.href = `/{self.resource_name}/create`;
                }}

                function editRecord(id) {{
                    window.location.href = `/{self.resource_name}/${{id}}/edit`;
                }}

                function deleteRecord(id) {{
                    if (confirm('Are you sure you want to delete this record?')) {{
                        fetch(`/api/{self.resource_name}/${{id}}`, {{ method: 'DELETE' }})
                            .then(() => location.reload());
                    }}
                }}

                // Request initial data
                ws.onopen = function() {{
                    ws.send(JSON.stringify({{ type: 'request_data' }}));
                }};

                // Also fetch data via HTTP as fallback
                fetch('/api/{self.resource_name}')
                    .then(response => response.json())
                    .then(data => {{
                        if (data.records && data.records.length > 0) {{
                            updateTable(data.records);
                        }}
                    }})
                    .catch(err => console.error('Error fetching initial data:', err));
            </script>
        </body>
        </html>
        """

    def generate_form_html(self, record_id: Optional[str] = None) -> str:
        """Generate HTML for create/edit form"""
        is_edit = record_id is not None
        title = f"Edit {self.resource_name.title()}" if is_edit else f"Create {self.resource_name.title()}"

        # Generate form fields
        form_fields = []
        for field_name, field_config in self.fields.items():
            if field_config.get('type') == 'primary_key' or field_config.get('auto_now', False) or field_config.get('auto_now_add', False):
                continue  # Skip auto fields

            field_type = field_config.get('type', 'string')
            required = ' required' if field_config.get('required', False) else ''

            if field_type == 'select':
                options = field_config.get('options', [])
                option_html = ''.join([f'<option value="{opt}">{opt}</option>' for opt in options])
                form_fields.append(f"""
                <div class="form-group">
                    <label for="{field_name}">{field_name.replace('_', ' ').title()}</label>
                    <select id="{field_name}" name="{field_name}"{required}>
                        <option value="">Select {field_name}</option>
                        {option_html}
                    </select>
                </div>
                """)
            elif field_type in ['text']:
                form_fields.append(f"""
                <div class="form-group">
                    <label for="{field_name}">{field_name.replace('_', ' ').title()}</label>
                    <textarea id="{field_name}" name="{field_name}"{required}></textarea>
                </div>
                """)
            else:
                input_type = {
                    'email': 'email',
                    'decimal': 'number',
                    'integer': 'number'
                }.get(field_type, 'text')

                step = ' step="0.01"' if field_type == 'decimal' else ''
                min_val = f' min="{field_config["min"]}"' if 'min' in field_config else ''
                max_val = f' max="{field_config["max"]}"' if 'max' in field_config else ''
                max_length = f' maxlength="{field_config["max_length"]}"' if 'max_length' in field_config else ''

                form_fields.append(f"""
                <div class="form-group">
                    <label for="{field_name}">{field_name.replace('_', ' ').title()}</label>
                    <input type="{input_type}" id="{field_name}" name="{field_name}"{required}{step}{min_val}{max_val}{max_length}>
                </div>
                """)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} - DBBasic CRUD</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #333; }}
                .back-btn {{ background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; }}
                .back-btn:hover {{ background: #545b62; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: 500; color: #333; }}
                input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }}
                textarea {{ height: 100px; resize: vertical; }}
                .form-actions {{ display: flex; gap: 10px; justify-content: flex-end; margin-top: 30px; }}
                .save-btn {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }}
                .save-btn:hover {{ background: #0056b3; }}
                .cancel-btn {{ background: #6c757d; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; }}
                .cancel-btn:hover {{ background: #545b62; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">{title}</div>
                    <a href="/{self.resource_name}" class="back-btn">← Back to List</a>
                </div>

                <form id="recordForm" onsubmit="saveRecord(event)">
                    {''.join(form_fields)}

                    <div class="form-actions">
                        <a href="/{self.resource_name}" class="cancel-btn">Cancel</a>
                        <button type="submit" class="save-btn">Save</button>
                    </div>
                </form>
            </div>

            <script>
                const isEdit = {str(is_edit).lower()};
                const recordId = {f"'{record_id}'" if record_id else 'null'};
                const resourceName = '{self.resource_name}';

                if (isEdit && recordId) {{
                    // Load existing record data
                    fetch(`/api/{self.resource_name}/${{recordId}}`)
                        .then(response => response.json())
                        .then(data => {{
                            for (const [key, value] of Object.entries(data)) {{
                                const field = document.getElementById(key);
                                if (field) field.value = value || '';
                            }}
                        }});
                }}

                function saveRecord(event) {{
                    event.preventDefault();
                    const formData = new FormData(event.target);
                    const data = Object.fromEntries(formData.entries());

                    const method = isEdit ? 'PUT' : 'POST';
                    const url = isEdit ? `/api/{self.resource_name}/${{recordId}}` : `/api/{self.resource_name}`;

                    fetch(url, {{
                        method: method,
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }})
                    .then(response => {{
                        if (response.ok) {{
                            window.location.href = '/{self.resource_name}';
                        }} else {{
                            alert('Error saving record');
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """

class CRUDEngine:
    """Main CRUD Engine that manages all resources and provides web interface"""

    def __init__(self):
        self.app = FastAPI(title="DBBasic CRUD Engine", version="1.0.0")
        self.resources: Dict[str, CRUDResource] = {}
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
        self.config_watcher = Observer()

        # Setup file watcher
        handler = CRUDConfigHandler(self)
        self.config_watcher.schedule(handler, ".", recursive=False)

        # Setup FastAPI routes
        self._setup_routes()

        # Load initial configurations
        self.load_all_configs()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/")
        async def dashboard():
            """Serve CRUD Engine dashboard using presentation layer"""
            ui_data = get_crud_dashboard()
            html_content = PresentationLayer.render(ui_data, 'bootstrap')
            return HTMLResponse(content=html_content)

        @self.app.get("/models/new")
        async def new_model_form():
            """Show form for creating a new CRUD model"""
            from dbbasic_unified_ui import get_master_layout

            ui_data = get_master_layout(
                title='Create New Model - Data Service',
                service_name='data',
                content=[
                    {
                        'type': 'breadcrumb',
                        'items': [
                            {'text': 'Data Service', 'url': '/'},
                            {'text': 'Create New Model', 'active': True}
                        ]
                    },
                    {
                        'type': 'card',
                        'title': '📝 Create New CRUD Model',
                        'body': {
                            'type': 'form',
                            'action': '/api/models/create',
                            'method': 'POST',
                            'fields': [
                                {
                                    'type': 'text',
                                    'name': 'resource',
                                    'label': 'Resource Name',
                                    'placeholder': 'e.g., products, orders, customers',
                                    'required': True,
                                    'help': 'Lowercase plural name for your model'
                                },
                                {
                                    'type': 'text',
                                    'name': 'title',
                                    'label': 'Display Title',
                                    'placeholder': 'e.g., Product Management',
                                    'required': True
                                },
                                {
                                    'type': 'textarea',
                                    'name': 'description',
                                    'label': 'Description',
                                    'placeholder': 'Brief description of what this model does',
                                    'rows': 3
                                },
                                {
                                    'type': 'textarea',
                                    'name': 'yaml_config',
                                    'label': 'YAML Configuration',
                                    'placeholder': '''fields:
  id:
    type: integer
    primary: true
  name:
    type: string
    required: true
  created_at:
    type: timestamp
    default: now''',
                                    'rows': 15,
                                    'help': 'Define your fields and configuration in YAML format'
                                }
                            ],
                            'buttons': [
                                {
                                    'type': 'submit',
                                    'text': 'Create Model',
                                    'variant': 'primary'
                                },
                                {
                                    'type': 'button',
                                    'text': 'Cancel',
                                    'variant': 'secondary',
                                    'onclick': 'history.back()'
                                }
                            ]
                        }
                    },
                    {
                        'type': 'card',
                        'title': '💡 Quick Tips',
                        'body': {
                            'type': 'list',
                            'items': [
                                'Resource names should be lowercase and plural',
                                'Each field needs a type (string, integer, boolean, etc.)',
                                'Use "required: true" for mandatory fields',
                                'Add "hooks" section for business logic',
                                'Check templates for examples'
                            ]
                        }
                    }
                ]
            )

            html_content = PresentationLayer.render(ui_data, 'bootstrap')
            return HTMLResponse(content=html_content)

        @self.app.get("/templates")
        async def templates_marketplace():
            """Show template marketplace with deployment functionality"""
            try:
                # Get available templates
                from pathlib import Path
                templates_dir = Path("templates")
                templates = []

                if templates_dir.exists():
                    for category_dir in templates_dir.iterdir():
                        if category_dir.is_dir():
                            category = category_dir.name
                            for template_file in category_dir.glob("*.yaml"):
                                template_name = template_file.stem.replace('_crud', '')
                                template_id = f"{category}/{template_file.stem}"

                                # Read template for metadata
                                try:
                                    with open(template_file, 'r') as f:
                                        config = yaml.safe_load(f)

                                    templates.append({
                                        'id': template_id,
                                        'name': template_name.replace('_', ' ').title(),
                                        'category': category.title(),
                                        'description': config.get('description', f"{category.title()} {template_name} management"),
                                        'resource': config.get('resource', template_name),
                                        'fields_count': len(config.get('fields', {})),
                                    })
                                except Exception as e:
                                    logger.warning(f"Error reading template {template_file}: {e}")

                # Build UI structure as data
                ui_structure = {
                    'type': 'page',
                    'title': 'DBBasic - Template Marketplace',
                    'components': [
                        {
                            'type': 'navbar',
                            'brand': 'DBBasic',
                            'links': [
                                {'text': 'Monitor', 'url': 'http://localhost:8004'},
                                {'text': 'Data', 'url': 'http://localhost:8005'},
                                {'text': 'AI Services', 'url': 'http://localhost:8003'},
                                {'text': 'Templates', 'url': '/templates'}
                            ]
                        },
                        {
                            'type': 'hero',
                            'title': '🛍️ Template Marketplace',
                            'subtitle': 'Deploy production-ready applications instantly'
                        },
                        {
                            'type': 'grid',
                            'columns': 3,
                            'items': [
                                {
                                    'type': 'card',
                                    'id': f"template-{t['id'].replace('/', '-')}",
                                    'title': t['name'],
                                    'category': t['category'],
                                    'description': f"{t['description']} • {t['fields_count']} fields",
                                    'body': f'''
                                        <div class="d-grid gap-2">
                                            <button class="btn btn-outline-primary" onclick="previewTemplate('{t['id']}')">
                                                <i class="bi bi-eye me-2"></i>Preview Config
                                            </button>
                                            <button class="btn btn-success" onclick="deployTemplate('{t['id']}')">
                                                <i class="bi bi-rocket-takeoff me-2"></i>Deploy
                                            </button>
                                        </div>
                                    '''
                                } for t in templates
                            ]
                        },
                        # Modal for preview
                        {
                            'type': 'raw',
                            'content': '''
                            <div class="modal fade" id="previewModal" tabindex="-1">
                                <div class="modal-dialog modal-lg modal-dialog-scrollable">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">
                                                <i class="bi bi-file-code me-2"></i>
                                                <span id="previewTitle">Template Preview</span>
                                            </h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div id="previewContent">
                                                <div class="text-center py-4">
                                                    <div class="spinner-border text-primary" role="status">
                                                        <span class="visually-hidden">Loading...</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                            <button type="button" class="btn btn-success" id="deployFromPreview">
                                                <i class="bi bi-rocket-takeoff me-2"></i>Deploy This Template
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            '''
                        },
                        # JavaScript for preview functionality
                        {
                            'type': 'script',
                            'content': '''
                            let currentTemplateId = null;

                            async function previewTemplate(templateId) {
                                currentTemplateId = templateId;
                                const modal = new bootstrap.Modal(document.getElementById('previewModal'));
                                modal.show();

                                // Update title
                                document.getElementById('previewTitle').textContent = `Template: ${templateId}`;

                                // Show loading
                                document.getElementById('previewContent').innerHTML = `
                                    <div class="text-center py-4">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                    </div>
                                `;

                                try {
                                    const response = await fetch(`/api/templates/${templateId}/preview`);
                                    const data = await response.json();

                                    // Display YAML with basic syntax highlighting
                                    const highlightedYaml = data.content
                                        .replace(/^(\w+):/gm, '<span class="text-primary fw-bold">$1</span>:')
                                        .replace(/: (.*)/g, ': <span class="text-success">$1</span>')
                                        .replace(/(#.*$)/gm, '<span class="text-muted fst-italic">$1</span>')
                                        .replace(/(\n  - )/g, '\n  <span class="text-warning">-</span> ');

                                    document.getElementById('previewContent').innerHTML = `
                                        <div class="mb-3">
                                            <div class="alert alert-info">
                                                <strong>Resource:</strong> ${data.metadata.resource}<br>
                                                <strong>Fields:</strong> ${data.metadata.fields_count}<br>
                                                <strong>Hooks:</strong> ${data.metadata.hooks_count || 0}
                                            </div>
                                        </div>
                                        <pre class="bg-dark text-light p-3 rounded" style="max-height: 500px; overflow-y: auto;">
                                            <code>${highlightedYaml}</code>
                                        </pre>
                                    `;

                                    // Set up deploy button
                                    document.getElementById('deployFromPreview').onclick = () => {
                                        modal.hide();
                                        deployTemplate(templateId);
                                    };

                                } catch (error) {
                                    document.getElementById('previewContent').innerHTML = `
                                        <div class="alert alert-danger">
                                            <i class="bi bi-exclamation-triangle me-2"></i>
                                            Error loading template: ${error.message}
                                        </div>
                                    `;
                                }
                            }

                            function deployTemplate(templateId) {
                                if (confirm(`Deploy template: ${templateId}?`)) {
                                    // Implementation for deployment
                                    fetch('/api/templates/deploy?template_id=' + encodeURIComponent(templateId), {
                                        method: 'POST'
                                    }).then(response => {
                                        if (response.ok) {
                                            alert('Template deployed successfully!');
                                            window.location.reload();
                                        } else {
                                            alert('Deployment failed. Check console for details.');
                                        }
                                    });
                                }
                            }
                            '''
                        }
                    ]
                }

                # Use presentation layer - can switch to 'tailwind' or custom later
                return HTMLResponse(PresentationLayer.render(ui_structure, 'bootstrap'))
            except Exception as e:
                logger.error(f"Error loading templates marketplace: {e}")
                raise HTTPException(500, f"Error loading templates: {e}")

        @self.app.get("/{resource_name}")
        async def resource_list(resource_name: str):
            """Show list view for a resource"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            # Use presentation layer with unified UI
            from dbbasic_unified_ui import get_master_layout
            resource = self.resources[resource_name]

            # Get resource fields for table headers
            list_display = resource.interface.get('list_display', list(resource.fields.keys())[:5])

            ui_data = get_master_layout(
                title=f'{resource_name.title()} - Data Service',
                service_name='data',
                content=[
                    {
                        'type': 'breadcrumb',
                        'items': [
                            {'text': 'Data Service', 'url': '/'},
                            {'text': resource_name.title(), 'active': True}
                        ]
                    },
                    {
                        'type': 'card',
                        'title': f'📋 {resource_name.title()} Records',
                        'body': {
                            'type': 'raw',
                            'content': f'''
                                <div class="d-flex justify-content-between mb-3">
                                    <div>
                                        <input type="text" class="form-control" placeholder="Search..." id="searchInput" style="width: 300px;">
                                    </div>
                                    <a href="/{resource_name}/create" class="btn btn-success">
                                        <i class="bi bi-plus-circle me-2"></i>Add New
                                    </a>
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-hover" id="dataTable">
                                        <thead>
                                            <tr>
                                                {' '.join([f'<th>{field.replace("_", " ").title()}</th>' for field in list_display])}
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="tableBody">
                                            <!-- Data will be loaded here -->
                                        </tbody>
                                    </table>
                                </div>
                            '''
                        }
                    }
                ],
                scripts=[
                    {
                        'type': 'script',
                        'content': f'''
                            // Load data for {resource_name}
                            async function loadData() {{
                                try {{
                                    const response = await fetch('/api/{resource_name}');
                                    const data = await response.json();
                                    const tbody = document.getElementById('tableBody');

                                    if (data.records && data.records.length > 0) {{
                                        tbody.innerHTML = data.records.map(record => {{
                                            const fields = {list_display};
                                            const values = fields.map(field => `<td>${{record[field] || ''}}</td>`).join('');
                                            return `
                                                <tr>
                                                    ${{values}}
                                                    <td>
                                                        <div class="btn-group btn-group-sm">
                                                            <a href="/{resource_name}/${{record.id}}/edit" class="btn btn-warning">
                                                                <i class="bi bi-pencil"></i>
                                                            </a>
                                                            <button class="btn btn-danger" onclick="deleteRecord(${{record.id}})">
                                                                <i class="bi bi-trash"></i>
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            `;
                                        }}).join('');
                                    }} else {{
                                        tbody.innerHTML = '<tr><td colspan="{len(list_display) + 1}" class="text-center">No records found</td></tr>';
                                    }}
                                }} catch (error) {{
                                    console.error('Error loading data:', error);
                                }}
                            }}

                            async function deleteRecord(id) {{
                                if (confirm('Are you sure you want to delete this record?')) {{
                                    try {{
                                        await fetch(`/api/{resource_name}/${{id}}`, {{ method: 'DELETE' }});
                                        loadData();
                                    }} catch (error) {{
                                        console.error('Error deleting record:', error);
                                    }}
                                }}
                            }}

                            // Search functionality
                            document.getElementById('searchInput').addEventListener('input', function(e) {{
                                const filter = e.target.value.toLowerCase();
                                const rows = document.querySelectorAll('#tableBody tr');
                                rows.forEach(row => {{
                                    const text = row.textContent.toLowerCase();
                                    row.style.display = text.includes(filter) ? '' : 'none';
                                }});
                            }});

                            // Load data on page load
                            document.addEventListener('DOMContentLoaded', loadData);
                        '''
                    }
                ]
            )

            html_content = PresentationLayer.render(ui_data, 'bootstrap')
            return HTMLResponse(content=html_content)

        @self.app.get("/{resource_name}/create")
        async def resource_create_form(resource_name: str):
            """Show create form for a resource"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")
            return HTMLResponse(self.resources[resource_name].generate_form_html())

        @self.app.get("/{resource_name}/{record_id}/edit")
        async def resource_edit_form(resource_name: str, record_id: str):
            """Show edit form for a resource"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")
            return HTMLResponse(self.resources[resource_name].generate_form_html(record_id))

        # API Endpoints - must come before generic routes
        @self.app.get("/api/models")
        async def api_get_models():
            """Get list of active CRUD models/resources"""
            models = []
            for resource_name, resource in self.resources.items():
                try:
                    # Get record count
                    count = len(resource.db.execute(f"SELECT COUNT(*) FROM {resource_name}").fetchall())

                    # Get fields from config
                    fields = list(resource.config.get('fields', {}).keys())

                    models.append({
                        'name': resource_name,
                        'title': resource.config.get('title', resource_name.title()),
                        'description': resource.config.get('description', f'{resource_name} management'),
                        'fields': fields,
                        'field_count': len(fields),
                        'record_count': count,
                        'database': resource.config.get('database', f'{resource_name}.db'),
                        'hooks': list(resource.config.get('hooks', {}).keys()),
                        'endpoint': f'/{resource_name}'
                    })
                except Exception as e:
                    logger.warning(f"Error getting model info for {resource_name}: {e}")
                    models.append({
                        'name': resource_name,
                        'error': str(e)
                    })

            return models

        # Template Marketplace APIs - must come before generic routes
        @self.app.get("/api/templates/{template_id:path}/preview")
        async def api_preview_template(template_id: str):
            """Get the YAML content of a template for preview"""
            try:
                from pathlib import Path

                # Validate and sanitize template_id
                if '..' in template_id or template_id.startswith('/'):
                    raise HTTPException(400, "Invalid template ID")

                # Parse template_id (e.g., "blog/posts_crud")
                if '/' not in template_id:
                    raise HTTPException(400, "Invalid template ID format. Expected: category/template")

                # Ensure template_id ends with _crud if not already
                if not template_id.endswith('_crud'):
                    parts = template_id.rsplit('/', 1)
                    if len(parts) == 2:
                        template_id = f"{parts[0]}/{parts[1]}_crud"

                template_path = Path(f"templates/{template_id}.yaml")

                if not template_path.exists():
                    raise HTTPException(404, f"Template not found: {template_id}")

                # Read the YAML content
                with open(template_path, 'r') as f:
                    yaml_content = f.read()

                # Parse to get metadata
                config = yaml.safe_load(yaml_content)

                return {
                    'id': template_id,
                    'content': yaml_content,
                    'metadata': {
                        'resource': config.get('resource', ''),
                        'title': config.get('title', ''),
                        'description': config.get('description', ''),
                        'fields_count': len(config.get('fields', {})),
                        'hooks_count': len(config.get('hooks', {}))
                    }
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error previewing template {template_id}: {e}")
                raise HTTPException(500, f"Error loading template: {e}")

        @self.app.get("/api/templates")
        async def api_get_templates():
            """Get list of available templates from the templates directory"""
            try:
                from pathlib import Path
                templates_dir = Path("templates")

                if not templates_dir.exists():
                    return {"templates": [], "categories": []}

                templates = []
                categories = set()

                # Scan template directories
                for category_dir in templates_dir.iterdir():
                    if category_dir.is_dir() and not category_dir.name.startswith('.'):
                        category_name = category_dir.name
                        categories.add(category_name)

                        # Scan template files in category
                        for template_file in category_dir.glob("*_crud.yaml"):
                            try:
                                with open(template_file, 'r') as f:
                                    template_config = yaml.safe_load(f)

                                resource_name = template_config.get('resource', template_file.stem.replace('_crud', ''))

                                template_info = {
                                    "id": f"{category_name}/{template_file.stem}",
                                    "name": resource_name.replace('_', ' ').title(),
                                    "description": f"Complete {resource_name} management system",
                                    "category": category_name,
                                    "file_path": str(template_file),
                                    "fields_count": len(template_config.get('fields', {})),
                                    "has_hooks": bool(template_config.get('hooks', {})),
                                    "has_permissions": bool(template_config.get('permissions', {})),
                                    "ui_theme": template_config.get('ui', {}).get('theme', 'bootstrap')
                                }
                                templates.append(template_info)

                            except Exception as e:
                                logger.warning(f"Error reading template {template_file}: {e}")

                return {
                    "templates": templates,
                    "categories": sorted(list(categories))
                }

            except Exception as e:
                logger.error(f"Error getting templates: {e}")
                raise HTTPException(500, f"Error getting templates: {e}")

        @self.app.post("/api/models/create")
        async def api_create_model(request: Request):
            """Create a new CRUD model from form data"""
            try:
                from pathlib import Path

                # Parse form data
                form_data = await request.form()
                resource = form_data.get('resource', '').strip()
                title = form_data.get('title', '')
                description = form_data.get('description', '')
                yaml_config = form_data.get('yaml_config', '')

                if not resource:
                    raise HTTPException(400, "Resource name is required")

                # Create the YAML configuration
                config_content = f"""# {title}
# {description}

resource: {resource}
title: {title}
description: {description}

{yaml_config}
"""

                # Save to a file
                filename = f"{resource}_crud.yaml"
                file_path = Path(filename)

                with open(file_path, 'w') as f:
                    f.write(config_content)

                # Load the new resource
                self.load_resource(filename)

                # Redirect to the new resource
                return RedirectResponse(url=f"/{resource}", status_code=303)

            except Exception as e:
                logger.error(f"Error creating model: {e}")
                raise HTTPException(500, f"Error creating model: {e}")

        @self.app.post("/api/templates/deploy")
        async def api_deploy_template(
            template_id: str = Query(..., description="Template ID in format category/template"),
            deployment_config: dict = {}
        ):
            """Deploy a template by copying it to the current directory and loading it"""
            try:
                from pathlib import Path
                import shutil
                import time

                # Parse template_id (e.g., "blog/posts_crud")
                if '/' not in template_id:
                    raise HTTPException(400, "Invalid template_id format. Expected: category/template")

                category, template_name = template_id.split('/', 1)
                template_file = Path(f"templates/{category}/{template_name}.yaml")

                if not template_file.exists():
                    raise HTTPException(404, f"Template not found: {template_id}")

                # Generate unique resource name for deployment
                base_name = deployment_config.get('resource_name', template_name.replace('_crud', ''))
                timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
                deployed_name = f"{base_name}_{timestamp}"
                deployed_file = Path(f"{deployed_name}_crud.yaml")

                # Copy template file to current directory
                shutil.copy2(template_file, deployed_file)

                # Customize the deployed template
                with open(deployed_file, 'r') as f:
                    config = yaml.safe_load(f)

                # Update resource name and database
                config['resource'] = deployed_name
                if 'database' in config:
                    original_db = config['database']
                    # Create unique database name
                    db_name = f"{deployed_name}.db"
                    config['database'] = db_name

                # Apply any custom configuration
                if deployment_config:
                    # Allow customizing certain fields
                    if 'title_override' in deployment_config:
                        # Find title-like fields and update descriptions
                        for field_name, field_config in config.get('fields', {}).items():
                            if field_name in ['title', 'name'] and 'ui' in field_config:
                                field_config['ui']['placeholder'] = deployment_config['title_override']

                # Write customized config back
                with open(deployed_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                # Load the new template into the engine
                self.load_config(str(deployed_file))

                logger.info(f"✅ Template deployed: {template_id} → {deployed_name}")

                return {
                    "success": True,
                    "resource_name": deployed_name,
                    "file_path": str(deployed_file),
                    "url": f"http://localhost:8005/{deployed_name}",
                    "api_url": f"http://localhost:8005/api/{deployed_name}",
                    "message": f"Template {template_id} deployed successfully as {deployed_name}"
                }

            except Exception as e:
                logger.error(f"❌ Error deploying template {template_id}: {e}")
                raise HTTPException(500, f"Error deploying template: {e}")

        @self.app.get("/api/templates/preview")
        async def api_preview_template(template_id: str = Query(..., description="Template ID in format category/template")):
            """Get a preview of a template's configuration and UI"""
            try:
                from pathlib import Path

                # Parse template_id
                if '/' not in template_id:
                    raise HTTPException(400, "Invalid template_id format. Expected: category/template")

                category, template_name = template_id.split('/', 1)
                template_file = Path(f"templates/{category}/{template_name}.yaml")

                if not template_file.exists():
                    raise HTTPException(404, f"Template not found: {template_id}")

                # Read template configuration
                with open(template_file, 'r') as f:
                    config = yaml.safe_load(f)

                # Generate preview data
                resource_name = config.get('resource', template_name.replace('_crud', ''))
                fields = config.get('fields', {})

                # Create sample preview data structure
                preview_data = {
                    "resource_name": resource_name,
                    "fields": list(fields.keys()),
                    "field_types": {name: field.get('type', 'string') for name, field in fields.items()},
                    "ui_components": {},
                    "has_hooks": bool(config.get('hooks', {})),
                    "hook_events": list(config.get('hooks', {}).keys()),
                    "permissions": config.get('permissions', {}),
                    "ui_theme": config.get('ui', {}).get('theme', 'bootstrap'),
                    "sample_form_fields": []
                }

                # Generate UI component preview
                for field_name, field_config in fields.items():
                    ui_config = field_config.get('ui', {})
                    component_type = ui_config.get('component', 'input')

                    preview_data['ui_components'][field_name] = {
                        "type": component_type,
                        "placeholder": ui_config.get('placeholder', ''),
                        "help_text": ui_config.get('help_text', ''),
                        "required": field_config.get('required', False)
                    }

                    # Sample form field for preview
                    preview_data['sample_form_fields'].append({
                        "name": field_name,
                        "label": field_name.replace('_', ' ').title(),
                        "type": component_type,
                        "value": f"Sample {field_name}"
                    })

                return preview_data

            except Exception as e:
                logger.error(f"❌ Error previewing template {template_id}: {e}")
                raise HTTPException(500, f"Error previewing template: {e}")

        # API routes for resources
        @self.app.get("/api/{resource_name}")
        async def api_list_records(resource_name: str, limit: int = Query(25), offset: int = Query(0), x_user: str = Header(None)):
            """Get records for a resource"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            # Check read permission
            if not self._check_permission(resource, 'read', x_user):
                raise HTTPException(403, "Permission denied")

            try:
                result = resource.db.execute(
                    f"SELECT * FROM {resource_name} LIMIT {limit} OFFSET {offset}"
                ).fetchall()

                # Convert to list of dicts
                columns = [desc[0] for desc in resource.db.description]
                records = [dict(zip(columns, row)) for row in result]

                return {"records": records, "total": len(result)}
            except Exception as e:
                raise HTTPException(500, f"Database error: {e}")

        @self.app.get("/api/{resource_name}/{record_id}")
        async def api_get_record(resource_name: str, record_id: str, x_user: str = Header(None)):
            """Get single record"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            # Check read permission
            if not self._check_permission(resource, 'read', x_user):
                raise HTTPException(403, "Permission denied")

            try:
                result = resource.db.execute(
                    f"SELECT * FROM {resource_name} WHERE id = ?", [record_id]
                ).fetchone()

                if not result:
                    raise HTTPException(404, "Record not found")

                columns = [desc[0] for desc in resource.db.description]
                return dict(zip(columns, result))
            except Exception as e:
                raise HTTPException(500, f"Database error: {e}")

        @self.app.post("/api/{resource_name}")
        async def api_create_record(resource_name: str, data: dict, x_user: str = Header(None)):
            """Create new record"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            # Check create permission
            if not self._check_permission(resource, 'create', x_user):
                raise HTTPException(403, "Permission denied")

            # Auto-populate magic fields
            data = self._populate_magic_fields(resource, data, 'create', x_user)

            # Execute hooks
            if 'before_create' in resource.hooks:
                await self._execute_hook(resource.hooks['before_create'], data)

            try:
                # For DuckDB, we need to generate the ID ourselves
                # Get next ID by finding max existing ID
                max_id_result = resource.db.execute(f"SELECT COALESCE(MAX(id), 0) FROM {resource_name}").fetchone()
                next_id = (max_id_result[0] if max_id_result else 0) + 1

                # Add the generated ID to the data
                data['id'] = next_id

                # Build insert query - include all fields including generated ID
                fields = [k for k in data.keys() if k in resource.fields]
                placeholders = ','.join(['?' for _ in fields])
                values = [data[f] for f in fields]

                # Execute the insert
                resource.db.execute(
                    f"INSERT INTO {resource_name} ({','.join(fields)}) VALUES ({placeholders})",
                    values
                )

                # Get the created record
                created_record = resource.db.execute(
                    f"SELECT * FROM {resource_name} WHERE id = ?", [next_id]
                ).fetchone()

                columns = [desc[0] for desc in resource.db.description]
                record_dict = dict(zip(columns, created_record))

                # Execute after hook
                if 'after_create' in resource.hooks:
                    await self._execute_hook(resource.hooks['after_create'], record_dict)

                # Notify WebSocket clients
                await self._broadcast_update(resource_name)

                return record_dict
            except Exception as e:
                raise HTTPException(500, f"Database error: {e}")

        @self.app.put("/api/{resource_name}/{record_id}")
        async def api_update_record(resource_name: str, record_id: int, data: dict, x_user: str = Header(None)):
            """Update existing record"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            # Check if record exists
            existing = resource.db.execute(f"SELECT * FROM {resource_name} WHERE id = ?", [record_id]).fetchone()
            if not existing:
                raise HTTPException(404, f"Record {record_id} not found")

            # Convert to dict for permission check
            columns = [desc[0] for desc in resource.db.description]
            existing_dict = dict(zip(columns, existing))

            # Check update permission
            if not self._check_permission(resource, 'update', x_user, existing_dict):
                raise HTTPException(403, "Permission denied")

            # Auto-populate magic fields for update
            data = self._populate_magic_fields(resource, data, 'update', x_user)

            # Execute hooks
            if 'before_update' in resource.hooks:
                await self._execute_hook(resource.hooks['before_update'], data)

            try:
                # Build update query
                fields = [k for k in data.keys() if k in resource.fields and k != 'id']
                set_clause = ','.join([f"{f} = ?" for f in fields])
                values = [data[f] for f in fields] + [record_id]

                # Execute the update
                resource.db.execute(
                    f"UPDATE {resource_name} SET {set_clause} WHERE id = ?",
                    values
                )

                # Execute after_update hook
                if 'after_update' in resource.hooks:
                    await self._execute_hook(resource.hooks['after_update'], data)

                # Broadcast real-time update
                await self._broadcast_update(resource_name)

                # Return updated record
                updated = resource.db.execute(f"SELECT * FROM {resource_name} WHERE id = ?", [record_id]).fetchone()
                columns = [desc[0] for desc in resource.db.description]
                return dict(zip(columns, updated))

            except Exception as e:
                logger.error(f"❌ Error updating record: {e}")
                raise HTTPException(500, f"Error updating record: {e}")

        @self.app.delete("/api/{resource_name}/{record_id}")
        async def api_delete_record(resource_name: str, record_id: int, x_user: str = Header(None)):
            """Delete record"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            # Check if record exists
            existing = resource.db.execute(f"SELECT * FROM {resource_name} WHERE id = ?", [record_id]).fetchone()
            if not existing:
                raise HTTPException(404, f"Record {record_id} not found")

            # Convert to dict for permission check
            columns = [desc[0] for desc in resource.db.description]
            existing_dict = dict(zip(columns, existing))

            # Check delete permission
            if not self._check_permission(resource, 'delete', x_user, existing_dict):
                raise HTTPException(403, "Permission denied")

            # Execute hooks
            if 'before_delete' in resource.hooks:
                await self._execute_hook(resource.hooks['before_delete'], existing_dict)

            try:
                # Execute the delete
                resource.db.execute(f"DELETE FROM {resource_name} WHERE id = ?", [record_id])

                # Execute after_delete hook
                if 'after_delete' in resource.hooks:
                    existing_data = dict(zip([desc[0] for desc in resource.db.description], existing))
                    await self._execute_hook(resource.hooks['after_delete'], existing_data)

                # Broadcast real-time update
                await self._broadcast_update(resource_name)

                return {"message": "Record deleted successfully", "id": record_id}

            except Exception as e:
                logger.error(f"❌ Error deleting record: {e}")
                raise HTTPException(500, f"Error deleting record: {e}")

        @self.app.get("/api/{resource_name}/export/csv")
        async def api_export_csv(resource_name: str):
            """Export all records as CSV"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            try:
                # Get all records
                result = resource.db.execute(f"SELECT * FROM {resource_name}").fetchall()
                columns = [desc[0] for desc in resource.db.description]

                # Create CSV in memory
                output = io.StringIO()
                writer = csv.writer(output)

                # Write header
                writer.writerow(columns)

                # Write data rows
                for row in result:
                    writer.writerow(row)

                # Prepare response
                csv_content = output.getvalue()
                output.close()

                return StreamingResponse(
                    io.StringIO(csv_content),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={resource_name}_export.csv"}
                )

            except Exception as e:
                logger.error(f"❌ Error exporting CSV: {e}")
                raise HTTPException(500, f"Error exporting CSV: {e}")

        @self.app.get("/api/{resource_name}/export/json")
        async def api_export_json(resource_name: str):
            """Export all records as JSON (for backup purposes)"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            try:
                # Get all records
                result = resource.db.execute(f"SELECT * FROM {resource_name}").fetchall()
                columns = [desc[0] for desc in resource.db.description]
                records = [dict(zip(columns, row)) for row in result]

                # Create backup structure with metadata
                backup_data = {
                    "resource": resource_name,
                    "exported_at": datetime.now().isoformat(),
                    "config": resource.config,
                    "total_records": len(records),
                    "records": records
                }

                json_content = json.dumps(backup_data, indent=2, default=str)

                return StreamingResponse(
                    io.StringIO(json_content),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={resource_name}_backup.json"}
                )

            except Exception as e:
                logger.error(f"❌ Error exporting JSON: {e}")
                raise HTTPException(500, f"Error exporting JSON: {e}")

        @self.app.post("/api/{resource_name}/import/csv")
        async def api_import_csv(
            resource_name: str,
            file: UploadFile = File(...),
            run_hooks: bool = Query(True, description="Execute hooks during import"),
            skip_validation: bool = Query(False, description="Skip validation hooks (only when run_hooks=True)")
        ):
            """Import records from CSV file with optional hook execution"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            try:
                # Read CSV content
                content = await file.read()
                csv_content = content.decode('utf-8')

                # Parse CSV
                csv_reader = csv.DictReader(io.StringIO(csv_content))

                imported_count = 0
                skipped_count = 0
                errors = []

                for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
                    try:
                        # Auto-populate magic fields for import
                        data = self._populate_magic_fields(resource, dict(row), 'create')

                        # Remove empty string values and convert to None
                        for key, value in data.items():
                            if value == '':
                                data[key] = None

                        # Handle ID field - generate if not present or empty
                        if 'id' not in data or data.get('id') in [None, '']:
                            # Generate ID like in the regular create endpoint
                            max_id_result = resource.db.execute(f"SELECT COALESCE(MAX(id), 0) FROM {resource_name}").fetchone()
                            next_id = (max_id_result[0] if max_id_result else 0) + imported_count + 1
                            data['id'] = next_id

                        # Execute before_create hook if enabled
                        if run_hooks and 'before_create' in resource.hooks:
                            try:
                                if not skip_validation or not resource.hooks['before_create'].endswith('_validation'):
                                    await self._execute_hook(resource.hooks['before_create'], data)
                            except Exception as hook_error:
                                errors.append(f"Row {row_num}: Hook validation failed - {str(hook_error)}")
                                skipped_count += 1
                                continue

                        # Build parameterized query
                        fields = list(data.keys())
                        placeholders = ', '.join(['?' for _ in fields])
                        field_names = ', '.join(fields)
                        values = [data[field] for field in fields]

                        # Insert record
                        result = resource.db.execute(
                            f"INSERT INTO {resource_name} ({field_names}) VALUES ({placeholders}) RETURNING *",
                            values
                        ).fetchone()

                        # Execute after_create hook if enabled
                        if run_hooks and 'after_create' in resource.hooks and result:
                            try:
                                columns = [desc[0] for desc in resource.db.description]
                                record_dict = dict(zip(columns, result))
                                await self._execute_hook(resource.hooks['after_create'], record_dict)
                            except Exception as hook_error:
                                # Log but don't fail - record is already created
                                logger.warning(f"After-create hook failed for row {row_num}: {hook_error}")

                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue

                # Broadcast real-time update if any records were imported
                if imported_count > 0:
                    await self._broadcast_update(resource_name)

                result = {
                    "message": f"Import completed",
                    "imported_records": imported_count,
                    "skipped_records": skipped_count,
                    "total_rows": row_num - 1 if 'row_num' in locals() else 0,
                    "hooks_executed": run_hooks,
                    "errors": errors[:10]  # Limit error messages
                }

                if errors:
                    result["error_count"] = len(errors)
                    if len(errors) > 10:
                        result["note"] = f"Showing first 10 of {len(errors)} errors"

                return result

            except Exception as e:
                logger.error(f"❌ Error importing CSV: {e}")
                raise HTTPException(500, f"Error importing CSV: {e}")

        @self.app.post("/api/{resource_name}/import/json")
        async def api_import_json(
            resource_name: str,
            file: UploadFile = File(...),
            run_hooks: bool = Query(True, description="Execute hooks during import"),
            skip_validation: bool = Query(False, description="Skip validation hooks")
        ):
            """Import records from JSON backup file with optional hook execution"""
            if resource_name not in self.resources:
                raise HTTPException(404, f"Resource '{resource_name}' not found")

            resource = self.resources[resource_name]

            try:
                # Read JSON content
                content = await file.read()
                json_content = content.decode('utf-8')
                backup_data = json.loads(json_content)

                # Validate backup structure
                if 'records' not in backup_data:
                    raise HTTPException(400, "Invalid backup file: missing 'records' field")

                records = backup_data['records']
                imported_count = 0
                skipped_count = 0
                errors = []

                for record_num, record in enumerate(records, start=1):
                    try:
                        # Auto-populate magic fields for import
                        data = self._populate_magic_fields(resource, dict(record), 'create')

                        # Handle ID field - generate if not present or empty
                        if 'id' not in data or data.get('id') in [None, '']:
                            # Generate ID like in the regular create endpoint
                            max_id_result = resource.db.execute(f"SELECT COALESCE(MAX(id), 0) FROM {resource_name}").fetchone()
                            next_id = (max_id_result[0] if max_id_result else 0) + imported_count + 1
                            data['id'] = next_id

                        # Execute before_create hook if enabled
                        if run_hooks and 'before_create' in resource.hooks:
                            try:
                                if not skip_validation or not resource.hooks['before_create'].endswith('_validation'):
                                    await self._execute_hook(resource.hooks['before_create'], data)
                            except Exception as hook_error:
                                errors.append(f"Record {record_num}: Hook validation failed - {str(hook_error)}")
                                skipped_count += 1
                                continue

                        # Build parameterized query
                        fields = list(data.keys())
                        placeholders = ', '.join(['?' for _ in fields])
                        field_names = ', '.join(fields)
                        values = [data[field] for field in fields]

                        # Insert record
                        result = resource.db.execute(
                            f"INSERT INTO {resource_name} ({field_names}) VALUES ({placeholders}) RETURNING *",
                            values
                        ).fetchone()

                        # Execute after_create hook if enabled
                        if run_hooks and 'after_create' in resource.hooks and result:
                            try:
                                columns = [desc[0] for desc in resource.db.description]
                                record_dict = dict(zip(columns, result))
                                await self._execute_hook(resource.hooks['after_create'], record_dict)
                            except Exception as hook_error:
                                # Log but don't fail - record is already created
                                logger.warning(f"After-create hook failed for record {record_num}: {hook_error}")

                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Record {record_num}: {str(e)}")
                        skipped_count += 1
                        continue

                # Broadcast real-time update if any records were imported
                if imported_count > 0:
                    await self._broadcast_update(resource_name)

                result = {
                    "message": f"Import completed",
                    "imported_records": imported_count,
                    "skipped_records": skipped_count,
                    "total_records": len(records),
                    "hooks_executed": run_hooks,
                    "backup_metadata": {
                        "original_resource": backup_data.get('resource'),
                        "exported_at": backup_data.get('exported_at'),
                        "original_total": backup_data.get('total_records')
                    },
                    "errors": errors[:10]  # Limit error messages
                }

                if errors:
                    result["error_count"] = len(errors)
                    if len(errors) > 10:
                        result["note"] = f"Showing first 10 of {len(errors)} errors"

                return result

            except Exception as e:
                logger.error(f"❌ Error importing JSON: {e}")
                raise HTTPException(500, f"Error importing JSON: {e}")

        @self.app.websocket("/ws/{resource_name}")
        async def websocket_endpoint(websocket: WebSocket, resource_name: str):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()

            if resource_name not in self.websocket_connections:
                self.websocket_connections[resource_name] = []
            self.websocket_connections[resource_name].append(websocket)

            try:
                while True:
                    data = await websocket.receive_json()
                    if data.get('type') == 'request_data':
                        # Send current data
                        if resource_name in self.resources:
                            resource = self.resources[resource_name]
                            try:
                                result = resource.db.execute(f"SELECT * FROM {resource_name}").fetchall()
                                columns = [desc[0] for desc in resource.db.description]
                                records = [dict(zip(columns, row)) for row in result]

                                await websocket.send_json({
                                    "type": "data_update",
                                    "records": records
                                })
                            except Exception as e:
                                logger.error(f"Error fetching data for WebSocket: {e}")
            except WebSocketDisconnect:
                if resource_name in self.websocket_connections:
                    self.websocket_connections[resource_name].remove(websocket)


    def _populate_magic_fields(self, resource: 'CRUDResource', data: dict, operation: str, user_id: str = None) -> dict:
        """Auto-populate magic fields like timestamps and user tracking"""
        now = datetime.now().isoformat()
        # For now, use a placeholder user ID since we don't have authentication yet
        current_user = user_id or "system"

        # Check each field in the resource configuration
        # Fields are stored as a dict with field names as keys
        for field_name, field_config in resource.fields.items():
            # Handle auto_now_add fields (only on create)
            if operation == 'create' and field_config.get('auto_now_add'):
                if field_config.get('type') == 'timestamp' and field_name not in data:
                    data[field_name] = now

            # Handle auto_now fields (on create and update)
            if field_config.get('auto_now'):
                if field_config.get('type') == 'timestamp':
                    data[field_name] = now

            # Handle ownership tracking fields
            if operation == 'create' and field_config.get('auto_user_add'):
                if field_name not in data:
                    data[field_name] = current_user

            if field_config.get('auto_user'):
                data[field_name] = current_user

        return data

    def _check_permission(self, resource: 'CRUDResource', operation: str, user_id: str = None, record: dict = None) -> bool:
        """Check if user has permission for the operation based on config"""
        # No permissions config means allow all
        if 'permissions' not in resource.config:
            return True

        permissions = resource.permissions
        permission_rule = permissions.get(operation, 'public')

        # Public permission - anyone can access
        if permission_rule == 'public':
            return True

        # Authenticated permission - must have a user ID
        if permission_rule == 'authenticated':
            return user_id is not None

        # Owner or admin permission
        if permission_rule == 'owner_or_admin':
            if not record:
                return False
            # Check if user is owner (look for created_by field)
            owner_field = None
            for field_name, field_config in resource.fields.items():
                if field_config.get('auto_user_add'):
                    owner_field = field_name
                    break
            if owner_field and record.get(owner_field) == user_id:
                return True
            # Check if user is admin (simplified - in real app would check user roles)
            if user_id and user_id.startswith('admin'):
                return True
            return False

        # Admin only permission
        if permission_rule == 'admin_only':
            return user_id and user_id.startswith('admin')

        # Default deny if unknown permission rule
        return False

    async def _execute_hook(self, hook_name: str, data: dict):
        """Execute a hook by calling the corresponding service"""
        try:
            # Check if service exists
            response = requests.get(f"http://localhost:8003/api/services/{hook_name}")
            if response.status_code == 404:
                logger.warning(f"🤖 Hook service '{hook_name}' not found, requesting AI generation...")
                # TODO: Integrate with AI Service Builder to generate missing hook
                return

            # Call the hook service
            hook_response = requests.post(
                f"http://localhost:8003/api/{hook_name}",
                json=data,
                timeout=30
            )

            if hook_response.status_code != 200:
                logger.error(f"❌ Hook '{hook_name}' failed: {hook_response.text}")
            else:
                logger.info(f"✅ Hook '{hook_name}' executed successfully")

        except Exception as e:
            logger.error(f"❌ Error executing hook '{hook_name}': {e}")

    async def _broadcast_update(self, resource_name: str):
        """Broadcast updates to all WebSocket clients for a resource"""
        if resource_name not in self.websocket_connections:
            return

        if resource_name in self.resources:
            resource = self.resources[resource_name]
            try:
                result = resource.db.execute(f"SELECT * FROM {resource_name}").fetchall()
                columns = [desc[0] for desc in resource.db.description]
                records = [dict(zip(columns, row)) for row in result]

                # Send to all connected clients
                for websocket in self.websocket_connections[resource_name][:]:
                    try:
                        await websocket.send_json({
                            "type": "data_update",
                            "records": records
                        })
                    except:
                        # Remove disconnected clients
                        self.websocket_connections[resource_name].remove(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting update: {e}")

    def load_all_configs(self):
        """Load all CRUD configuration files"""
        config_files = list(Path(".").glob("*_crud.yaml"))
        for config_file in config_files:
            self.load_config(str(config_file))

    def load_config(self, config_path: str):
        """Load a CRUD configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            resource_name = config['resource']
            self.resources[resource_name] = CRUDResource(config_path, config)
            logger.info(f"✅ Loaded CRUD config: {resource_name}")

        except Exception as e:
            logger.error(f"❌ Error loading config {config_path}: {e}")

    async def reload_config(self, config_path: str):
        """Reload a changed configuration file"""
        self.load_config(config_path)

        # Broadcast updates to all clients
        for resource_name in self.resources.keys():
            await self._broadcast_update(resource_name)

    def start_watching(self):
        """Start watching for config file changes"""
        self.config_watcher.start()
        logger.info("🔍 Started watching for CRUD config changes...")

    def stop_watching(self):
        """Stop watching for config file changes"""
        self.config_watcher.stop()
        self.config_watcher.join()

def main():
    """Run the CRUD Engine"""
    engine = CRUDEngine()
    engine.start_watching()

    try:
        logger.info("🚀 Starting DBBasic CRUD Engine on http://localhost:8005")
        uvicorn.run(engine.app, host="0.0.0.0", port=8005, log_level="info")
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down CRUD Engine...")
    finally:
        engine.stop_watching()

if __name__ == "__main__":
    main()