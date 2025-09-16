#!/usr/bin/env python3
"""
DBBasic YAML Parser - The Model-Config Revolution

Rails generators gave us 20% of an app. This gives us 100%.
The difference? Real-time, service-oriented, and complete coverage.
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import polars as pl
import duckdb

@dataclass
class TableDef:
    """Table definition from config"""
    name: str
    fields: List[str]
    indexes: List[str] = field(default_factory=list)
    relations: Dict[str, str] = field(default_factory=dict)
    computed: Dict[str, str] = field(default_factory=dict)
    workflow: Optional[Dict] = None

@dataclass
class ViewDef:
    """View/query definition"""
    name: str
    query: str
    type: str = "table"
    refresh: Optional[int] = None

@dataclass
class FormDef:
    """Form definition"""
    name: str
    fields: Any  # Can be 'auto' or list of fields
    validation: Dict[str, str] = field(default_factory=dict)
    actions: Dict[str, str] = field(default_factory=dict)

@dataclass
class AgentDef:
    """Autonomous agent definition"""
    name: str
    task: str
    schedule: Optional[str] = None
    trigger: Optional[str] = None
    output: Optional[str] = None

class DBBasicYAMLParser:
    """
    The parser that turns config into applications.
    This is where Rails stopped and DBBasic continues.
    """

    def __init__(self):
        self.config = {}
        self.tables: Dict[str, TableDef] = {}
        self.views: Dict[str, ViewDef] = {}
        self.forms: Dict[str, FormDef] = {}
        self.agents: Dict[str, AgentDef] = {}
        self.workflows = {}
        self.permissions = {}
        self.integrations = {}

    def load_file(self, path: str) -> Dict:
        """Load a .dbbasic YAML file"""
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f)
        self._parse_all()
        return self.config

    def load_string(self, yaml_str: str) -> Dict:
        """Load config from YAML string"""
        self.config = yaml.safe_load(yaml_str)
        self._parse_all()
        return self.config

    def _parse_all(self):
        """Parse all sections of the config"""
        if 'model' in self.config:
            self._parse_model()
        if 'views' in self.config:
            self._parse_views()
        if 'forms' in self.config:
            self._parse_forms()
        if 'agents' in self.config:
            self._parse_agents()
        if 'workflows' in self.config:
            self.workflows = self.config['workflows']
        if 'permissions' in self.config:
            self.permissions = self.config['permissions']
        if 'integrations' in self.config:
            self.integrations = self.config['integrations']

    def _parse_model(self):
        """Parse model section - the data structure"""
        model = self.config['model']

        for table_name, table_def in model.items():
            if isinstance(table_def, list):
                # Simple format: users: [id, name, email]
                self.tables[table_name] = TableDef(
                    name=table_name,
                    fields=table_def
                )
            else:
                # Complex format with metadata
                self.tables[table_name] = TableDef(
                    name=table_name,
                    fields=table_def.get('fields', []),
                    indexes=table_def.get('indexes', []),
                    relations=table_def.get('relations', {}),
                    computed=table_def.get('computed', {}),
                    workflow=table_def.get('workflow')
                )

    def _parse_views(self):
        """Parse views section - the queries"""
        views = self.config['views']

        for view_name, view_def in views.items():
            if isinstance(view_def, str):
                # Simple: dashboard: "SELECT * FROM orders"
                self.views[view_name] = ViewDef(
                    name=view_name,
                    query=view_def
                )
            elif isinstance(view_def, dict):
                # Complex with metadata
                if isinstance(view_def, dict) and len(view_def) == 1:
                    # Nested views like executive: {revenue_mtd: "..."}
                    for sub_name, sub_query in view_def.items():
                        full_name = f"{view_name}_{sub_name}"
                        self.views[full_name] = ViewDef(
                            name=full_name,
                            query=sub_query
                        )
                else:
                    self.views[view_name] = ViewDef(
                        name=view_name,
                        query=view_def.get('query', ''),
                        type=view_def.get('type', 'table'),
                        refresh=view_def.get('refresh')
                    )

    def _parse_forms(self):
        """Parse forms section"""
        forms = self.config['forms']

        for form_name, form_def in forms.items():
            if form_def == 'auto':
                # Auto-generate from table
                self.forms[form_name] = FormDef(
                    name=form_name,
                    fields='auto'
                )
            else:
                self.forms[form_name] = FormDef(
                    name=form_name,
                    fields=form_def.get('fields', []),
                    validation=form_def.get('validation', {}),
                    actions=form_def.get('actions', {})
                )

    def _parse_agents(self):
        """Parse agents section - autonomous operations"""
        agents = self.config['agents']

        for agent_name, agent_def in agents.items():
            self.agents[agent_name] = AgentDef(
                name=agent_name,
                schedule=agent_def.get('schedule'),
                trigger=agent_def.get('trigger'),
                task=agent_def.get('task', agent_def.get('action', '')),
                output=agent_def.get('output')
            )

    def generate_sql_schema(self) -> str:
        """Generate SQL CREATE statements"""
        sql = []

        for table in self.tables.values():
            columns = []
            for field_name in table.fields:
                field_type = self._infer_sql_type(field_name)
                columns.append(f"    {field_name} {field_type}")

            # Add foreign keys
            for fk_field, reference in table.relations.items():
                columns.append(f"    FOREIGN KEY ({fk_field}) REFERENCES {reference}")

            create_sql = f"CREATE TABLE {table.name} (\n"
            create_sql += ",\n".join(columns)
            create_sql += "\n);"
            sql.append(create_sql)

            # Add indexes
            for idx_field in table.indexes:
                sql.append(f"CREATE INDEX idx_{table.name}_{idx_field} ON {table.name}({idx_field});")

        # Add views
        for view in self.views.values():
            sql.append(f"CREATE VIEW {view.name} AS\n{view.query};")

        return "\n\n".join(sql)

    def _infer_sql_type(self, field_name: str) -> str:
        """Infer SQL type from field name"""
        fn = field_name.lower()

        if fn == 'id' or fn.endswith('_id'):
            return 'INTEGER PRIMARY KEY' if fn == 'id' else 'INTEGER'
        elif 'email' in fn:
            return 'VARCHAR(255)'
        elif 'name' in fn or 'title' in fn or 'sku' in fn:
            return 'VARCHAR(200)'
        elif 'description' in fn or 'content' in fn or 'notes' in fn:
            return 'TEXT'
        elif 'price' in fn or 'amount' in fn or 'total' in fn or 'revenue' in fn:
            return 'DECIMAL(10,2)'
        elif 'stock' in fn or 'count' in fn or 'quantity' in fn:
            return 'INTEGER'
        elif 'created' in fn or 'updated' in fn or 'date' in fn:
            return 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        elif 'status' in fn or 'state' in fn or 'stage' in fn:
            return 'VARCHAR(50)'
        elif 'phone' in fn:
            return 'VARCHAR(20)'
        elif 'industry' in fn or 'category' in fn or 'type' in fn:
            return 'VARCHAR(100)'
        else:
            return 'VARCHAR(255)'

    def generate_fastapi_routes(self) -> str:
        """Generate FastAPI route code"""
        code = []
        code.append("# Auto-generated FastAPI routes from DBBasic config")
        code.append("from fastapi import FastAPI, HTTPException")
        code.append("from typing import List, Optional")
        code.append("")
        code.append("# CRUD routes for each table")

        for table in self.tables.values():
            code.append(f"\n# {table.name.upper()} endpoints")
            code.append(f"@app.get('/api/{table.name}')")
            code.append(f"async def list_{table.name}():")
            code.append(f"    return engine.query('SELECT * FROM {table.name}')")
            code.append("")
            code.append(f"@app.get('/api/{table.name}/{{id}}')")
            code.append(f"async def get_{table.name}(id: int):")
            code.append(f"    return engine.query('SELECT * FROM {table.name} WHERE id = ?', [id])")
            code.append("")
            code.append(f"@app.post('/api/{table.name}')")
            code.append(f"async def create_{table.name}(data: dict):")
            code.append(f"    return engine.insert('{table.name}', data)")
            code.append("")
            code.append(f"@app.put('/api/{table.name}/{{id}}')")
            code.append(f"async def update_{table.name}(id: int, data: dict):")
            code.append(f"    return engine.update('{table.name}', id, data)")
            code.append("")
            code.append(f"@app.delete('/api/{table.name}/{{id}}')")
            code.append(f"async def delete_{table.name}(id: int):")
            code.append(f"    return engine.delete('{table.name}', id)")

        # View endpoints
        code.append("\n# VIEW endpoints")
        for view in self.views.values():
            code.append(f"@app.get('/api/views/{view.name}')")
            code.append(f"async def view_{view.name}():")
            code.append(f"    return engine.query('''{view.query}''')")
            code.append("")

        return "\n".join(code)

    def generate_html_form(self, form_name: str) -> str:
        """Generate HTML form from config"""
        if form_name not in self.forms:
            return ""

        form = self.forms[form_name]

        if form.fields == 'auto':
            # Auto-generate from table
            table_name = form_name.replace('_form', '')
            if table_name not in self.tables:
                return ""

            table = self.tables[table_name]
            html = [f'<form id="{form_name}" class="dbbasic-form">']
            html.append(f'  <h2>{table_name.title()}</h2>')

            for field in table.fields:
                if field == 'id':
                    continue
                field_type = self._infer_input_type(field)
                label = field.replace('_', ' ').title()
                html.append(f'  <div class="form-field">')
                html.append(f'    <label>{label}</label>')
                if field_type == 'textarea':
                    html.append(f'    <textarea name="{field}"></textarea>')
                else:
                    html.append(f'    <input type="{field_type}" name="{field}">')
                html.append(f'  </div>')

            html.append('  <button type="submit">Save</button>')
            html.append('</form>')
            return '\n'.join(html)

        # Manual form definition
        html = [f'<form id="{form_name}">']
        for field in form.fields:
            html.append(f'  <div class="form-field">')
            html.append(f'    <label>{field}</label>')
            html.append(f'    <input name="{field}">')
            html.append(f'  </div>')
        html.append('  <button type="submit">Submit</button>')
        html.append('</form>')
        return '\n'.join(html)

    def _infer_input_type(self, field_name: str) -> str:
        """Infer HTML input type from field name"""
        fn = field_name.lower()

        if 'email' in fn:
            return 'email'
        elif 'password' in fn:
            return 'password'
        elif 'phone' in fn or 'tel' in fn:
            return 'tel'
        elif 'url' in fn or 'link' in fn:
            return 'url'
        elif 'date' in fn or 'created' in fn or 'updated' in fn:
            return 'date'
        elif 'price' in fn or 'amount' in fn or 'stock' in fn or 'quantity' in fn:
            return 'number'
        elif 'description' in fn or 'notes' in fn or 'content' in fn:
            return 'textarea'
        else:
            return 'text'

    def summary(self) -> str:
        """Generate a summary of parsed config"""
        lines = []
        lines.append(f"DBBasic Config Summary")
        lines.append(f"=" * 40)
        lines.append(f"Tables: {len(self.tables)}")
        for t in self.tables.values():
            lines.append(f"  - {t.name}: {len(t.fields)} fields")

        lines.append(f"\nViews: {len(self.views)}")
        for v in self.views.values():
            lines.append(f"  - {v.name}")

        lines.append(f"\nForms: {len(self.forms)}")
        for f in self.forms.values():
            lines.append(f"  - {f.name}")

        lines.append(f"\nAgents: {len(self.agents)}")
        for a in self.agents.values():
            lines.append(f"  - {a.name}: {a.task}")

        lines.append(f"\nWorkflows: {len(self.workflows)}")
        lines.append(f"Permissions: {len(self.permissions)} rules")
        lines.append(f"Integrations: {len(self.integrations)}")

        return "\n".join(lines)