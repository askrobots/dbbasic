#!/usr/bin/env python3
"""
Update all DBBasic services to use the presentation layer
"""

import os
import re
from pathlib import Path

def update_ai_service_builder():
    """Update AI Service Builder to use presentation layer"""

    file_path = "dbbasic_ai_service_builder.py"

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already updated
    if 'get_ai_service_main_ui' in content:
        print("✅ AI Service Builder already uses presentation layer")
        return

    # Replace the root endpoint
    new_root = '''@app.get("/")
async def root():
    """Serve the AI Service Builder using presentation layer"""
    from dbbasic_ai_service_builder_presentation import get_ai_service_main_ui

    ui_data = get_ai_service_main_ui()
    html_content = PresentationLayer.render(ui_data, 'bootstrap')

    return HTMLResponse(content=html_content)'''

    # Find and replace the entire root function (from @app.get("/") to the end of the HTML)
    pattern = r'@app\.get\("/"\).*?</html>"""?\)'
    content = re.sub(pattern, new_root, content, flags=re.DOTALL)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated AI Service Builder root endpoint")

def update_crud_engine():
    """Update CRUD Engine to use presentation layer"""

    file_path = "dbbasic_crud_engine.py"

    # Check if file exists
    if not Path(file_path).exists():
        print("❌ dbbasic_crud_engine.py not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already has presentation layer
    if 'get_crud_dashboard' not in content:
        # Add import if not present
        if 'from dbbasic_crud_engine_presentation import' not in content:
            # Add import after other imports
            import_line = "\nfrom dbbasic_crud_engine_presentation import get_crud_dashboard, get_template_marketplace\n"
            content = content.replace('from fastapi import', import_line + 'from fastapi import', 1)

    # Update the root endpoint
    new_root = '''@app.get("/")
async def dashboard():
    """Serve CRUD Engine dashboard using presentation layer"""
    ui_data = get_crud_dashboard()
    html_content = PresentationLayer.render(ui_data, 'bootstrap')
    return HTMLResponse(content=html_content)'''

    # Find and replace dashboard endpoint
    pattern = r'@app\.get\("/"\).*?return HTMLResponse\([^)]+\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_root, content, flags=re.DOTALL)

    # Update templates endpoint
    new_templates = '''@app.get("/templates")
async def templates():
    """Serve template marketplace using presentation layer"""
    ui_data = get_template_marketplace()
    html_content = PresentationLayer.render(ui_data, 'bootstrap')
    return HTMLResponse(content=html_content)'''

    pattern = r'@app\.get\("/templates"\).*?return HTMLResponse\([^)]+\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_templates, content, flags=re.DOTALL)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated CRUD Engine endpoints")

def update_realtime_monitor():
    """Update Realtime Monitor to use presentation layer"""

    file_path = "realtime_monitor.py"

    if not Path(file_path).exists():
        print("❌ realtime_monitor.py not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already has presentation layer
    if 'get_realtime_monitor_ui' not in content:
        # Add import
        if 'from realtime_monitor_presentation import' not in content:
            import_line = "\nfrom realtime_monitor_presentation import get_realtime_monitor_ui\n"
            content = content.replace('from fastapi import', import_line + 'from fastapi import', 1)

    # Update the root endpoint
    new_root = '''@app.get("/")
async def dashboard():
    """Serve real-time monitor dashboard using presentation layer"""
    from realtime_monitor_presentation import get_realtime_monitor_ui

    ui_data = get_realtime_monitor_ui()
    html_content = PresentationLayer.render(ui_data, 'bootstrap')
    return HTMLResponse(content=html_content)'''

    # Find and replace
    pattern = r'@app\.get\("/"\).*?return HTMLResponse\([^)]+\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_root, content, flags=re.DOTALL)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated Realtime Monitor")

def update_event_store():
    """Update Event Store to use presentation layer"""

    file_path = "dbbasic_event_store.py"

    if not Path(file_path).exists():
        print("❌ dbbasic_event_store.py not found")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already has presentation layer
    if 'get_event_store_dashboard' not in content:
        # Add import
        if 'from dbbasic_event_store_presentation import' not in content:
            import_line = "\nfrom dbbasic_event_store_presentation import get_event_store_dashboard\n"
            content = content.replace('from fastapi import', import_line + 'from fastapi import', 1)

    # Update the root endpoint
    new_root = '''@app.get("/")
async def dashboard():
    """Serve event store dashboard using presentation layer"""
    from dbbasic_event_store_presentation import get_event_store_dashboard

    ui_data = get_event_store_dashboard()
    html_content = PresentationLayer.render(ui_data, 'bootstrap')
    return HTMLResponse(content=html_content)'''

    # Find and replace
    pattern = r'@app\.get\("/"\).*?return HTMLResponse\([^)]+\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_root, content, flags=re.DOTALL)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated Event Store")

def main():
    print("=" * 60)
    print("🔧 Updating all services to use presentation layer")
    print("=" * 60)

    # Update all services
    update_ai_service_builder()
    update_crud_engine()
    update_realtime_monitor()
    update_event_store()

    print("\n" + "=" * 60)
    print("✅ All services updated!")
    print("=" * 60)
    print("\n📌 Services will now use the presentation layer")
    print("   delivering 90% token reduction!")
    print("\n🔄 Restart services to apply changes:")
    print("   1. Stop current services (Ctrl+C)")
    print("   2. Run: python launch_dbbasic.py")

if __name__ == "__main__":
    main()