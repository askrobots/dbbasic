#!/usr/bin/env python3
"""
DBBasic Route Display
Shows all routes generated from DBBasic config files
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Route:
    """Represents a single route in the system"""
    path: str
    method: str = "GET"
    description: str = ""
    source_type: str = ""  # 'page', 'api', 'form', 'view', 'crud'
    config_file: str = ""
    auth_required: bool = False
    params: List[str] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = []

class RouteExtractor:
    """Extracts routes from DBBasic config files"""
    
    def __init__(self):
        self.routes = []
        
    def extract_from_config(self, config_path: str) -> List[Route]:
        """Extract all routes from a DBBasic config file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if not config:
            return []
            
        routes = []
        config_name = Path(config_path).name
        
        # Extract from pages section
        if 'pages' in config:
            for path, page_config in config.get('pages', {}).items():
                if not path.startswith('/'):
                    path = '/' + path
                    
                description = "Page"
                if isinstance(page_config, dict):
                    description = page_config.get('description', 'Page')
                    auth = page_config.get('auth', False)
                else:
                    auth = False
                    
                routes.append(Route(
                    path=path,
                    method="GET",
                    description=description,
                    source_type="page",
                    config_file=config_name,
                    auth_required=auth
                ))
        
        # Extract from API section
        if 'api' in config:
            for endpoint, api_config in config.get('api', {}).items():
                if not endpoint.startswith('/'):
                    endpoint = '/api/' + endpoint
                elif not endpoint.startswith('/api'):
                    endpoint = '/api' + endpoint
                    
                if isinstance(api_config, dict):
                    # Handle multiple HTTP methods
                    if 'operations' in api_config:
                        for method, desc in api_config['operations'].items():
                            routes.append(Route(
                                path=endpoint,
                                method=method.upper(),
                                description=desc,
                                source_type="api",
                                config_file=config_name,
                                auth_required=api_config.get('security', {}).get('auth', False)
                            ))
                    else:
                        # Single method API
                        method = api_config.get('method', 'GET')
                        routes.append(Route(
                            path=endpoint,
                            method=method.upper(),
                            description=api_config.get('description', 'API endpoint'),
                            source_type="api",
                            config_file=config_name,
                            auth_required=api_config.get('auth', False)
                        ))
        
        # Extract from forms section
        if 'forms' in config:
            for form_name, form_config in config.get('forms', {}).items():
                # Forms typically generate both GET (display) and POST (submit) routes
                path = f"/forms/{form_name}"
                
                routes.append(Route(
                    path=path,
                    method="GET",
                    description=f"Display {form_name} form",
                    source_type="form",
                    config_file=config_name
                ))
                
                routes.append(Route(
                    path=path,
                    method="POST",
                    description=f"Submit {form_name} form",
                    source_type="form",
                    config_file=config_name
                ))
        
        # Extract CRUD routes from data/model section
        if 'data' in config or 'model' in config:
            data_section = config.get('data', config.get('model', {}))
            for entity_name, entity_config in data_section.items():
                if isinstance(entity_config, dict) or isinstance(entity_config, list):
                    # Generate standard CRUD routes
                    base_path = f"/api/{entity_name}"
                    
                    routes.extend([
                        Route(
                            path=base_path,
                            method="GET",
                            description=f"List all {entity_name}",
                            source_type="crud",
                            config_file=config_name
                        ),
                        Route(
                            path=base_path,
                            method="POST",
                            description=f"Create new {entity_name}",
                            source_type="crud",
                            config_file=config_name
                        ),
                        Route(
                            path=f"{base_path}/{{id}}",
                            method="GET",
                            description=f"Get {entity_name} by ID",
                            source_type="crud",
                            config_file=config_name,
                            params=["id"]
                        ),
                        Route(
                            path=f"{base_path}/{{id}}",
                            method="PUT",
                            description=f"Update {entity_name}",
                            source_type="crud",
                            config_file=config_name,
                            params=["id"]
                        ),
                        Route(
                            path=f"{base_path}/{{id}}",
                            method="DELETE",
                            description=f"Delete {entity_name}",
                            source_type="crud",
                            config_file=config_name,
                            params=["id"]
                        )
                    ])
        
        # Extract from views section (typically read-only endpoints)
        if 'views' in config:
            for view_name, view_config in config.get('views', {}).items():
                path = f"/views/{view_name}"
                
                if isinstance(view_config, str):
                    # Simple SQL view
                    description = f"View: {view_name}"
                elif isinstance(view_config, dict):
                    description = view_config.get('description', f"View: {view_name}")
                else:
                    description = f"View: {view_name}"
                    
                routes.append(Route(
                    path=path,
                    method="GET",
                    description=description,
                    source_type="view",
                    config_file=config_name
                ))
        
        return routes
    
    def extract_from_directory(self, directory: str = ".") -> List[Route]:
        """Extract routes from all DBBasic config files in a directory"""
        all_routes = []
        
        # Look for .dbbasic and .yaml files that appear to be DBBasic configs
        for config_file in Path(directory).glob("*.dbbasic"):
            all_routes.extend(self.extract_from_config(str(config_file)))
            
        for config_file in Path(directory).glob("*.yaml"):
            # Check if it looks like a DBBasic config
            try:
                with open(config_file, 'r') as f:
                    content = yaml.safe_load(f)
                    if content and any(key in content for key in ['pages', 'api', 'data', 'model', 'forms', 'views']):
                        all_routes.extend(self.extract_from_config(str(config_file)))
            except:
                pass
                
        return all_routes

class RouteDisplay:
    """Display routes in various formats"""
    
    @staticmethod
    def as_table(routes: List[Route]) -> str:
        """Display routes as a formatted table"""
        if not routes:
            return "No routes found."
            
        # Calculate column widths
        method_width = max(len(r.method) for r in routes) + 2
        path_width = max(len(r.path) for r in routes) + 2
        desc_width = max(len(r.description) for r in routes if r.description) + 2
        type_width = max(len(r.source_type) for r in routes) + 2
        
        # Limit widths for readability
        path_width = min(path_width, 40)
        desc_width = min(desc_width, 40)
        
        # Header
        output = []
        output.append("=" * (method_width + path_width + desc_width + type_width + 10))
        output.append(f"{'Method':<{method_width}} {'Path':<{path_width}} {'Type':<{type_width}} {'Description':<{desc_width}}")
        output.append("=" * (method_width + path_width + desc_width + type_width + 10))
        
        # Routes
        for route in sorted(routes, key=lambda r: (r.path, r.method)):
            path = route.path[:path_width-2] if len(route.path) > path_width-2 else route.path
            desc = route.description[:desc_width-2] if len(route.description) > desc_width-2 else route.description
            output.append(
                f"{route.method:<{method_width}} {path:<{path_width}} {route.source_type:<{type_width}} {desc:<{desc_width}}"
            )
            
        output.append("=" * (method_width + path_width + desc_width + type_width + 10))
        output.append(f"Total: {len(routes)} routes")
        
        return "\n".join(output)
    
    @staticmethod
    def as_markdown(routes: List[Route]) -> str:
        """Display routes as markdown table"""
        if not routes:
            return "No routes found."
            
        output = []
        output.append("# DBBasic Routes")
        output.append("")
        output.append("| Method | Path | Type | Description | Auth | Config |")
        output.append("|--------|------|------|-------------|------|--------|")
        
        for route in sorted(routes, key=lambda r: (r.path, r.method)):
            auth = "✓" if route.auth_required else ""
            output.append(
                f"| {route.method} | {route.path} | {route.source_type} | {route.description} | {auth} | {route.config_file} |"
            )
            
        output.append("")
        output.append(f"**Total: {len(routes)} routes**")
        
        return "\n".join(output)
    
    @staticmethod
    def as_json(routes: List[Route]) -> str:
        """Export routes as JSON"""
        routes_dict = [
            asdict(route) for route in sorted(routes, key=lambda r: (r.path, r.method))
        ]
        return json.dumps(routes_dict, indent=2)
    
    @staticmethod
    def as_openapi_snippet(routes: List[Route]) -> str:
        """Generate OpenAPI specification snippet"""
        paths = {}
        
        for route in routes:
            if route.path not in paths:
                paths[route.path] = {}
                
            operation = {
                "summary": route.description,
                "tags": [route.source_type],
                "responses": {
                    "200": {"description": "Success"}
                }
            }
            
            if route.auth_required:
                operation["security"] = [{"bearerAuth": []}]
                
            if route.params:
                operation["parameters"] = [
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                    for param in route.params
                ]
                
            paths[route.path][route.method.lower()] = operation
            
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": "DBBasic API",
                "version": "1.0.0",
                "description": "Routes generated from DBBasic config"
            },
            "paths": paths
        }
        
        return yaml.dump(openapi, default_flow_style=False)

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Display routes from DBBasic config files")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to config file or directory (default: current directory)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["table", "markdown", "json", "openapi"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    extractor = RouteExtractor()
    
    # Extract routes
    path = Path(args.path)
    if path.is_file():
        routes = extractor.extract_from_config(str(path))
    else:
        routes = extractor.extract_from_directory(str(path))
    
    # Format output
    if args.format == "table":
        output = RouteDisplay.as_table(routes)
    elif args.format == "markdown":
        output = RouteDisplay.as_markdown(routes)
    elif args.format == "json":
        output = RouteDisplay.as_json(routes)
    elif args.format == "openapi":
        output = RouteDisplay.as_openapi_snippet(routes)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Routes written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()