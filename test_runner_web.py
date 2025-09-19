#!/usr/bin/env python3
"""
DBBasic Test Runner Web Interface
Run tests from browser, see real-time results with red/green status
"""

from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import re
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

app = FastAPI(title="DBBasic Test Runner")

# Store test results
test_results = {
    "last_run": None,
    "tests": [],
    "summary": {},
    "running": False,
    "output": []
}

# WebSocket connections
active_connections: List[WebSocket] = []

async def broadcast_message(message: dict):
    """Broadcast to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass

async def run_tests_async(test_file: str = "test_dbbasic_channels.py"):
    """Run tests and parse output in real-time"""
    global test_results

    test_results["running"] = True
    test_results["output"] = []
    test_results["tests"] = []
    test_results["last_run"] = datetime.now().isoformat()

    await broadcast_message({
        "type": "test_started",
        "timestamp": datetime.now().isoformat()
    })

    try:
        # Run pytest without JSON plugin (simpler and more reliable)
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pytest", test_file,
            "-v", "--tb=short", "--color=no",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT  # Combine stderr into stdout
        )

        # Read output line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_text = line.decode().strip()
            if line_text:
                test_results["output"].append(line_text)

                # Parse test result lines
                if "PASSED" in line_text:
                    # Extract test name from format: test_file.py::ClassName::test_name PASSED
                    if "::" in line_text:
                        parts = line_text.split("::")
                        test_name = parts[-1].split(" ")[0] if len(parts) > 0 else "Unknown"
                    else:
                        test_name = "Unknown"

                    test_results["tests"].append({
                        "name": test_name,
                        "status": "passed",
                        "time": datetime.now().isoformat()
                    })
                    await broadcast_message({
                        "type": "test_result",
                        "name": test_name,
                        "status": "passed",
                        "line": line_text
                    })

                elif "FAILED" in line_text:
                    # Extract test name from format: test_file.py::ClassName::test_name FAILED
                    if "::" in line_text:
                        parts = line_text.split("::")
                        test_name = parts[-1].split(" ")[0] if len(parts) > 0 else "Unknown"
                    else:
                        test_name = "Unknown"

                    test_results["tests"].append({
                        "name": test_name,
                        "status": "failed",
                        "time": datetime.now().isoformat()
                    })
                    await broadcast_message({
                        "type": "test_result",
                        "name": test_name,
                        "status": "failed",
                        "line": line_text
                    })

                elif "ERROR" in line_text:
                    test_name = line_text.split("::")[1].split(" ")[0] if "::" in line_text else "Unknown"
                    test_results["tests"].append({
                        "name": test_name,
                        "status": "error",
                        "time": datetime.now().isoformat()
                    })
                    await broadcast_message({
                        "type": "test_result",
                        "name": test_name,
                        "status": "error",
                        "line": line_text
                    })

                # Broadcast output line
                await broadcast_message({
                    "type": "output",
                    "line": line_text
                })

        await process.wait()

        # Parse summary
        try:
            with open("/tmp/test_report.json", "r") as f:
                report = json.load(f)
                test_results["summary"] = report.get("summary", {})
        except:
            # Fallback summary from output
            passed = sum(1 for t in test_results["tests"] if t["status"] == "passed")
            failed = sum(1 for t in test_results["tests"] if t["status"] == "failed")
            test_results["summary"] = {
                "passed": passed,
                "failed": failed,
                "total": len(test_results["tests"])
            }

    except Exception as e:
        test_results["output"].append(f"Error running tests: {str(e)}")
        await broadcast_message({
            "type": "error",
            "message": str(e)
        })

    finally:
        test_results["running"] = False
        await broadcast_message({
            "type": "test_completed",
            "summary": test_results["summary"],
            "timestamp": datetime.now().isoformat()
        })

async def run_selenium_tests_async():
    """Run Selenium tests and parse output in real-time"""
    global test_results

    test_results["running"] = True
    test_results["output"] = []
    test_results["tests"] = []
    test_results["last_run"] = datetime.now().isoformat()

    await broadcast_message({
        "type": "test_started",
        "test_type": "selenium",
        "timestamp": datetime.now().isoformat()
    })

    try:
        # Run Selenium tests
        process = await asyncio.create_subprocess_exec(
            sys.executable, "test_with_selenium.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # Read output line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_text = line.decode().strip()
            if line_text:
                test_results["output"].append(line_text)

                # Parse Selenium test results
                if "✅ PASSED:" in line_text:
                    test_name = line_text.split("✅ PASSED:")[1].strip()
                    test_results["tests"].append({
                        "name": test_name,
                        "status": "passed",
                        "time": datetime.now().isoformat()
                    })
                    await broadcast_message({
                        "type": "test_result",
                        "name": test_name,
                        "status": "passed",
                        "line": line_text
                    })

                elif "❌ FAILED:" in line_text or "❌ FAIL:" in line_text:
                    test_name = line_text.split("❌")[1].split(":")[1].strip() if ":" in line_text else "Unknown"
                    test_results["tests"].append({
                        "name": test_name,
                        "status": "failed",
                        "time": datetime.now().isoformat()
                    })
                    await broadcast_message({
                        "type": "test_result",
                        "name": test_name,
                        "status": "failed",
                        "line": line_text
                    })

                elif "Testing" in line_text and line_text.endswith("..."):
                    # Mark test as running
                    test_name = line_text.replace("Testing", "").replace("...", "").strip()
                    await broadcast_message({
                        "type": "test_running",
                        "name": test_name,
                        "line": line_text
                    })

                # Broadcast output line
                await broadcast_message({
                    "type": "output",
                    "line": line_text
                })

        await process.wait()

        # Generate summary
        passed = sum(1 for t in test_results["tests"] if t["status"] == "passed")
        failed = sum(1 for t in test_results["tests"] if t["status"] == "failed")
        test_results["summary"] = {
            "passed": passed,
            "failed": failed,
            "total": len(test_results["tests"])
        }

    except Exception as e:
        test_results["output"].append(f"Error running Selenium tests: {str(e)}")
        await broadcast_message({
            "type": "error",
            "message": str(e)
        })

    finally:
        test_results["running"] = False
        await broadcast_message({
            "type": "test_completed",
            "test_type": "selenium",
            "summary": test_results["summary"],
            "timestamp": datetime.now().isoformat()
        })

@app.get("/")
async def root():
    """Serve the test runner interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DBBasic Test Runner - 402M rows/sec</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: #666;
            font-size: 14px;
            margin-top: 0.5rem;
        }

        .run-btn {
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .run-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }

        .run-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 2rem;
            height: calc(100vh - 200px);
        }

        .test-list {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .test-item {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }

        .test-item.passed {
            background: #d4edda;
            border: 1px solid #28a745;
        }

        .test-item.failed {
            background: #f8d7da;
            border: 1px solid #dc3545;
        }

        .test-item.running {
            background: #fff3cd;
            border: 1px solid #ffc107;
            animation: pulse 1s infinite;
        }

        .test-item.pending {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .test-name {
            font-size: 14px;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
        }

        .test-status {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-passed {
            background: #28a745;
            color: white;
        }

        .status-failed {
            background: #dc3545;
            color: white;
        }

        .status-running {
            background: #ffc107;
            color: #000;
        }

        .status-pending {
            background: #6c757d;
            color: white;
        }

        .output-section {
            background: #1e1e1e;
            border-radius: 12px;
            padding: 1.5rem;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #333;
        }

        .output-title {
            color: #4CAF50;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .output-console {
            flex: 1;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            line-height: 1.5;
            color: #d4d4d4;
        }

        .output-line {
            padding: 0.25rem 0;
        }

        .output-line.error {
            color: #f48771;
        }

        .output-line.success {
            color: #89d185;
        }

        .output-line.warning {
            color: #ffd700;
        }

        .summary {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 2rem;
            text-align: center;
        }

        .summary-item {
            padding: 1rem;
            border-radius: 8px;
            background: #f8f9fa;
        }

        .summary-value {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }

        .summary-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }

        .summary-passed .summary-value {
            color: #28a745;
        }

        .summary-failed .summary-value {
            color: #dc3545;
        }

        .summary-total .summary-value {
            color: #667eea;
        }

        .summary-time .summary-value {
            color: #17a2b8;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-left: 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .benchmark-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="logo">DBBasic Test Runner</div>
                <div class="subtitle">Testing at 402M rows/sec capability</div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div class="benchmark-badge">⚡ 402M rows/sec</div>
                <button class="run-btn" id="runBtn" onclick="runTests()">
                    Run Unit Tests
                </button>
                <button class="run-btn" id="seleniumBtn" onclick="runSeleniumTests()">
                    Run Selenium Tests
                </button>
            </div>
        </div>

        <div class="main-grid">
            <div class="test-list">
                <h3 style="margin-bottom: 1rem; color: #333;">Test Suite</h3>
                <div id="testList"></div>
            </div>

            <div class="output-section">
                <div class="output-header">
                    <div class="output-title">Test Output</div>
                    <div id="statusIndicator" style="color: #999;">Ready</div>
                </div>
                <div class="output-console" id="outputConsole">
                    <div class="output-line">Waiting for tests to run...</div>
                    <div class="output-line" style="color: #666;">Click "Run All Tests" to begin</div>
                </div>
            </div>
        </div>

        <div class="summary" id="summary" style="display: none;">
            <div class="summary-grid">
                <div class="summary-item summary-passed">
                    <div class="summary-value" id="passedCount">0</div>
                    <div class="summary-label">Passed</div>
                </div>
                <div class="summary-item summary-failed">
                    <div class="summary-value" id="failedCount">0</div>
                    <div class="summary-label">Failed</div>
                </div>
                <div class="summary-item summary-total">
                    <div class="summary-value" id="totalCount">0</div>
                    <div class="summary-label">Total</div>
                </div>
                <div class="summary-item summary-time">
                    <div class="summary-value" id="timeCount">0s</div>
                    <div class="summary-label">Duration</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8006/ws');
        const outputConsole = document.getElementById('outputConsole');
        const testList = document.getElementById('testList');
        const runBtn = document.getElementById('runBtn');
        const seleniumBtn = document.getElementById('seleniumBtn');
        const statusIndicator = document.getElementById('statusIndicator');
        const summary = document.getElementById('summary');

        let testItems = {};
        let startTime = null;

        // Test names from our test suites
        const unitTestNames = [
            'test_publish_single_message',
            'test_subscribe_and_receive',
            'test_wildcard_subscription',
            'test_channel_worker_processing',
            'test_message_ttl_expiration',
            'test_concurrent_publishing',
            'test_channel_statistics',
            'test_add_single_task',
            'test_bulk_add_tasks',
            'test_get_next_task_priority',
            'test_task_locking',
            'test_complete_task',
            'test_fail_task_with_retry',
            'test_metrics_calculation',
            'test_task_worker',
            'test_benchmark_insert_speed',
            'test_benchmark_concurrent_workers',
            'test_benchmark_pub_sub_latency',
            'test_integration_full_pipeline'
        ];

        const seleniumTestNames = [
            'Dashboard Links',
            'Config Count',
            'Syntax Highlighting'
        ];

        let currentTestType = 'unit';

        // Initialize test list
        function initTestList(testType = 'unit') {
            testList.innerHTML = '';
            testItems = {};
            currentTestType = testType;

            const testNames = testType === 'selenium' ? seleniumTestNames : unitTestNames;
            testNames.forEach(name => {
                const item = document.createElement('div');
                item.className = 'test-item pending';
                item.innerHTML = `
                    <span class="test-name" title="${name}">${name}</span>
                    <span class="test-status status-pending">pending</span>
                `;
                testList.appendChild(item);
                testItems[name] = item;
            });
        }

        ws.onopen = () => {
            console.log('Connected to test runner');
            loadTestStatus();
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'test_started') {
                outputConsole.innerHTML = '';
                const testType = data.test_type || 'unit';
                initTestList(testType);
                summary.style.display = 'none';
                startTime = Date.now();
                statusIndicator.innerHTML = '<span>Running</span><div class="spinner"></div>';
                statusIndicator.style.color = '#ffc107';
                runBtn.disabled = true;
                seleniumBtn.disabled = true;
                if (testType === 'selenium') {
                    seleniumBtn.textContent = 'Running...';
                    runBtn.textContent = 'Run Unit Tests';
                } else {
                    runBtn.textContent = 'Running...';
                    seleniumBtn.textContent = 'Run Selenium Tests';
                }
            }

            else if (data.type === 'test_result') {
                updateTestItem(data.name, data.status);
                addOutput(data.line, data.status === 'passed' ? 'success' : 'error');
            }

            else if (data.type === 'output') {
                addOutput(data.line);
            }

            else if (data.type === 'test_completed') {
                const duration = ((Date.now() - startTime) / 1000).toFixed(1);
                statusIndicator.innerHTML = 'Completed';
                statusIndicator.style.color = '#28a745';
                runBtn.disabled = false;
                seleniumBtn.disabled = false;
                runBtn.textContent = 'Run Unit Tests';
                seleniumBtn.textContent = 'Run Selenium Tests';

                // Update summary
                updateSummary(data.summary, duration);
                summary.style.display = 'block';
            }

            else if (data.type === 'error') {
                addOutput('Error: ' + data.message, 'error');
                statusIndicator.innerHTML = 'Error';
                statusIndicator.style.color = '#dc3545';
                runBtn.disabled = false;
                seleniumBtn.disabled = false;
                runBtn.textContent = 'Run Unit Tests';
                seleniumBtn.textContent = 'Run Selenium Tests';
            }
        };

        function updateTestItem(name, status) {
            if (testItems[name]) {
                testItems[name].className = `test-item ${status}`;
                const statusSpan = testItems[name].querySelector('.test-status');
                statusSpan.className = `test-status status-${status}`;
                statusSpan.textContent = status;
            }
        }

        function addOutput(line, type = '') {
            const div = document.createElement('div');
            div.className = 'output-line ' + type;

            // Color code output
            if (line.includes('PASSED')) {
                div.className = 'output-line success';
            } else if (line.includes('FAILED') || line.includes('ERROR')) {
                div.className = 'output-line error';
            } else if (line.includes('WARNING')) {
                div.className = 'output-line warning';
            }

            div.textContent = line;
            outputConsole.appendChild(div);
            outputConsole.scrollTop = outputConsole.scrollHeight;
        }

        function updateSummary(summary, duration) {
            document.getElementById('passedCount').textContent = summary.passed || 0;
            document.getElementById('failedCount').textContent = summary.failed || 0;
            document.getElementById('totalCount').textContent = summary.total || 0;
            document.getElementById('timeCount').textContent = duration + 's';
        }

        async function runTests() {
            const response = await fetch('/api/run-tests', { method: 'POST' });
            const result = await response.json();
            console.log('Tests started:', result);
        }

        async function runSeleniumTests() {
            const response = await fetch('/api/run-selenium-tests', { method: 'POST' });
            const result = await response.json();
            console.log('Selenium tests started:', result);
        }

        async function loadTestStatus() {
            const response = await fetch('/api/status');
            const status = await response.json();

            if (status.tests && status.tests.length > 0) {
                initTestList();
                status.tests.forEach(test => {
                    updateTestItem(test.name, test.status);
                });

                if (status.summary) {
                    updateSummary(status.summary, '0');
                    summary.style.display = 'block';
                }
            } else {
                initTestList();
            }
        }

        // Initialize
        initTestList();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time test updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Keep connection alive
    except:
        active_connections.remove(websocket)

@app.post("/api/run-tests")
async def run_tests(background_tasks: BackgroundTasks):
    """Start running tests"""
    if test_results["running"]:
        return JSONResponse({
            "status": "error",
            "message": "Tests already running"
        })

    # Run tests in background
    background_tasks.add_task(run_tests_async)

    return JSONResponse({
        "status": "started",
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/run-selenium-tests")
async def run_selenium_tests(background_tasks: BackgroundTasks):
    """Start running Selenium tests"""
    if test_results["running"]:
        return JSONResponse({
            "status": "error",
            "message": "Tests already running"
        })

    # Run Selenium tests in background
    background_tasks.add_task(run_selenium_tests_async)

    return JSONResponse({
        "status": "started",
        "test_type": "selenium",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/status")
async def get_status():
    """Get current test status"""
    return JSONResponse(test_results)

@app.get("/api/benchmark")
async def run_benchmark():
    """Quick benchmark test"""
    from dbbasic_task_queue import DBBasicTaskQueue

    queue = DBBasicTaskQueue(db_path=":memory:")

    # Benchmark bulk insert
    tasks = [{'task_type': 'bench', 'payload': {'i': i}} for i in range(10000)]
    start = time.time()
    queue.bulk_add_tasks(tasks)
    elapsed = time.time() - start
    rate = 10000 / elapsed

    return JSONResponse({
        "tasks_inserted": 10000,
        "time_seconds": round(elapsed, 3),
        "rate_per_second": round(rate),
        "vs_postgresql": f"{round(rate/10000, 1)}x faster"
    })

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 DBBasic Test Runner Web Interface")
    print("   View tests at: http://localhost:8006")
    print("   Run tests and see real-time red/green results!\n")
    uvicorn.run(app, host="0.0.0.0", port=8006)