#!/usr/bin/env python3
"""
DBBasic Unified Design System - Bootstrap 5.3
Shared HTML templates and styling for all DBBasic services
"""

# Bootstrap 5.3.3 CDN links (latest stable version)
BOOTSTRAP_CSS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
BOOTSTRAP_JS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"

# DBBasic Brand Colors
BRAND_COLORS = {
    "primary": "#0d6efd",      # Bootstrap primary blue
    "secondary": "#6c757d",    # Bootstrap secondary gray
    "success": "#198754",      # Bootstrap success green
    "info": "#0dcaf0",         # Bootstrap info cyan
    "warning": "#ffc107",      # Bootstrap warning yellow
    "danger": "#dc3545",       # Bootstrap danger red
    "light": "#f8f9fa",        # Bootstrap light gray
    "dark": "#212529",         # Bootstrap dark gray
    "dbbasic": "#667eea",      # Custom DBBasic gradient start
    "dbbasic_end": "#764ba2"   # Custom DBBasic gradient end
}

def get_base_html_template(title: str, service_name: str, port: int, active_nav: str = "") -> str:
    """
    Generate the base HTML template with Bootstrap 5.3 and unified navigation

    Args:
        title: Page title
        service_name: Name of the current service (Data, AI Services, Monitor, etc.)
        port: Port number of current service
        active_nav: Which nav item should be marked as active
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <!-- Bootstrap 5.3.3 CSS -->
    <link href="{BOOTSTRAP_CSS}" rel="stylesheet"
          integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
          crossorigin="anonymous">

    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">

    <!-- Custom DBBasic Styles -->
    <style>
        :root {{
            --dbbasic-primary: {BRAND_COLORS["dbbasic"]};
            --dbbasic-secondary: {BRAND_COLORS["dbbasic_end"]};
            --dbbasic-gradient: linear-gradient(135deg, var(--dbbasic-primary) 0%, var(--dbbasic-secondary) 100%);
        }}

        .dbbasic-gradient {{
            background: var(--dbbasic-gradient);
        }}

        .dbbasic-navbar {{
            background: var(--dbbasic-gradient) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .dbbasic-card {{
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .dbbasic-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }}

        .service-badge {{
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
        }}

        .performance-badge {{
            background: var(--dbbasic-gradient);
            color: white;
            border: none;
        }}

        .navbar-brand {{
            font-weight: bold;
            font-size: 1.5rem;
        }}

        .nav-link {{
            font-weight: 500;
            transition: all 0.2s;
        }}

        .nav-link:hover {{
            background-color: rgba(255,255,255,0.1);
            border-radius: 0.375rem;
        }}

        .btn-dbbasic {{
            background: var(--dbbasic-gradient);
            border: none;
            color: white;
            font-weight: 500;
        }}

        .btn-dbbasic:hover {{
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            color: white;
        }}

        .table-dbbasic thead {{
            background: var(--dbbasic-gradient);
            color: white;
        }}

        .footer {{
            background-color: var(--bs-gray-100);
            margin-top: auto;
        }}
    </style>
</head>
<body class="d-flex flex-column min-vh-100">

    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg dbbasic-navbar">
        <div class="container-fluid">
            <a class="navbar-brand text-white" href="http://localhost:{port}">
                <i class="bi bi-database-fill me-2"></i>DBBasic
            </a>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                    data-bs-target="#navbarNav" aria-controls="navbarNav"
                    aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link text-white{'active' if active_nav == 'monitor' else ''}"
                           href="http://localhost:8004">
                            <i class="bi bi-speedometer2 me-1"></i>Monitor
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link text-white{'active' if active_nav == 'data' else ''}"
                           href="http://localhost:8005">
                            <i class="bi bi-table me-1"></i>Data
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link text-white{'active' if active_nav == 'ai' else ''}"
                           href="http://localhost:8003">
                            <i class="bi bi-robot me-1"></i>AI Services
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link text-white{'active' if active_nav == 'events' else ''}"
                           href="http://localhost:8006">
                            <i class="bi bi-journal-code me-1"></i>Events
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link text-white{'active' if active_nav == 'templates' else ''}"
                           href="http://localhost:8005/templates">
                            <i class="bi bi-collection me-1"></i>Templates
                        </a>
                    </li>
                </ul>

                <div class="d-flex align-items-center">
                    <span class="badge performance-badge me-3">
                        <i class="bi bi-lightning-fill me-1"></i>402M rows/sec
                    </span>
                    <span class="badge service-badge bg-light text-dark">
                        {service_name}
                    </span>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content Area -->
    <main class="flex-grow-1">
"""

def get_footer_template() -> str:
    """Generate the unified footer template"""
    return """
    </main>

    <!-- Footer -->
    <footer class="footer py-3 mt-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <small class="text-muted">
                        <i class="bi bi-database-fill me-1"></i>
                        DBBasic - Configuration-Driven Application Framework
                    </small>
                </div>
                <div class="col-md-6 text-md-end">
                    <small class="text-muted">
                        <i class="bi bi-github me-1"></i>
                        <a href="https://github.com/askrobots/dbbasic" class="text-decoration-none">
                            Open Source
                        </a>
                    </small>
                </div>
            </div>
        </div>
    </footer>

    <!-- Bootstrap 5.3.3 JS -->
    <script src="{BOOTSTRAP_JS}"
            integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
            crossorigin="anonymous"></script>

    <!-- Custom DBBasic JS -->
    <script>
        // Initialize all Bootstrap tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

        // Initialize all Bootstrap popovers
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    </script>
</body>
</html>
"""

def get_service_card(title: str, description: str, url: str, icon: str = "bi-gear",
                    status: str = "active", stats: str = "") -> str:
    """Generate a Bootstrap service card component"""
    status_class = "success" if status == "active" else "secondary"
    return f"""
    <div class="col">
        <div class="card dbbasic-card h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="card-title">
                        <i class="{icon} me-2"></i>{title}
                    </h5>
                    <span class="badge bg-{status_class}">{status}</span>
                </div>
                <p class="card-text">{description}</p>
                {f'<small class="text-muted">{stats}</small>' if stats else ''}
            </div>
            <div class="card-footer bg-transparent">
                <a href="{url}" class="btn btn-dbbasic">
                    <i class="bi bi-arrow-right me-1"></i>Access
                </a>
            </div>
        </div>
    </div>
    """

def get_template_card(title: str, description: str, category: str,
                     deploy_action: str = "", preview_action: str = "") -> str:
    """Generate a Bootstrap template card for the marketplace"""
    return f"""
    <div class="col">
        <div class="card dbbasic-card h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="card-title">{title}</h5>
                    <span class="badge bg-primary">{category}</span>
                </div>
                <p class="card-text">{description}</p>
            </div>
            <div class="card-footer bg-transparent">
                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                    {f'<button class="btn btn-outline-secondary btn-sm" {preview_action}><i class="bi bi-eye me-1"></i>Preview</button>' if preview_action else ''}
                    <button class="btn btn-dbbasic btn-sm" {deploy_action}>
                        <i class="bi bi-rocket-takeoff me-1"></i>Deploy
                    </button>
                </div>
            </div>
        </div>
    </div>
    """

def get_alert(message: str, alert_type: str = "info", dismissible: bool = True) -> str:
    """Generate a Bootstrap alert component"""
    icons = {
        "success": "bi-check-circle-fill",
        "danger": "bi-exclamation-triangle-fill",
        "warning": "bi-exclamation-triangle-fill",
        "info": "bi-info-circle-fill"
    }
    icon = icons.get(alert_type, "bi-info-circle-fill")
    dismissible_class = "alert-dismissible" if dismissible else ""
    dismiss_button = """
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    """ if dismissible else ""

    return f"""
    <div class="alert alert-{alert_type} {dismissible_class}" role="alert">
        <i class="{icon} me-2"></i>{message}
        {dismiss_button}
    </div>
    """

def get_breadcrumb(items: list) -> str:
    """Generate a Bootstrap breadcrumb component"""
    breadcrumb_items = []
    for i, item in enumerate(items):
        if i == len(items) - 1:  # Last item (current page)
            breadcrumb_items.append(f'<li class="breadcrumb-item active" aria-current="page">{item["text"]}</li>')
        else:
            breadcrumb_items.append(f'<li class="breadcrumb-item"><a href="{item["url"]}">{item["text"]}</a></li>')

    return f"""
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            {"".join(breadcrumb_items)}
        </ol>
    </nav>
    """

# Export commonly used components and templates
__all__ = [
    'BOOTSTRAP_CSS', 'BOOTSTRAP_JS', 'BRAND_COLORS',
    'get_base_html_template', 'get_footer_template',
    'get_service_card', 'get_template_card', 'get_alert', 'get_breadcrumb'
]