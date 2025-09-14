"""Minimal web UI for monitoring Reddit bot status and activity."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS


class BotMonitor:
    """Simple monitoring system for the Reddit bot."""
    
    def __init__(self):
        self.status = "stopped"  # stopped, running, paused, error
        self.start_time: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        self.stats = {
            "posts_checked": 0,
            "responses_generated": 0,
            "successful_replies": 0,
            "failed_replies": 0,
            "keywords_matched": 0
        }
        self.recent_activity: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.current_subreddits = ["india", "AskReddit"]
        self.active_providers = []
        
    def update_status(self, status: str):
        """Update bot status."""
        self.status = status
        if status == "running" and not self.start_time:
            self.start_time = datetime.now()
        elif status == "stopped":
            self.start_time = None
        
        self.last_activity = datetime.now()
    
    def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log bot activity."""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "details": details
        }
        
        self.recent_activity.insert(0, activity)
        
        # Keep only last 50 activities
        if len(self.recent_activity) > 50:
            self.recent_activity = self.recent_activity[:50]
        
        self.last_activity = datetime.now()
    
    def log_error(self, error_msg: str, details: Optional[Dict[str, Any]] = None):
        """Log error."""
        error = {
            "timestamp": datetime.now().isoformat(),
            "message": error_msg,
            "details": details or {}
        }
        
        self.errors.insert(0, error)
        
        # Keep only last 20 errors
        if len(self.errors) > 20:
            self.errors = self.errors[:20]
    
    def increment_stat(self, stat_name: str, amount: int = 1):
        """Increment a statistic."""
        if stat_name in self.stats:
            self.stats[stat_name] += amount
    
    def get_uptime(self) -> Optional[str]:
        """Get bot uptime as human-readable string."""
        if not self.start_time:
            return None
        
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


# Global monitor instance
monitor = BotMonitor()

# Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def dashboard():
    """Main dashboard."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """Get current bot status."""
    return jsonify({
        "status": monitor.status,
        "uptime": monitor.get_uptime(),
        "last_activity": monitor.last_activity.isoformat() if monitor.last_activity else None,
        "stats": monitor.stats,
        "subreddits": monitor.current_subreddits,
        "providers": monitor.active_providers
    })


@app.route('/api/activity')
def api_activity():
    """Get recent activity."""
    limit = min(int(request.args.get('limit', 20)), 50)
    return jsonify({
        "activities": monitor.recent_activity[:limit]
    })


@app.route('/api/errors')
def api_errors():
    """Get recent errors."""
    limit = min(int(request.args.get('limit', 10)), 20)
    return jsonify({
        "errors": monitor.errors[:limit]
    })


@app.route('/api/control/<action>', methods=['POST'])
def api_control(action):
    """Bot control endpoints."""
    if action == "start":
        monitor.update_status("running")
        monitor.log_activity("control", {"action": "started_via_ui"})
        return jsonify({"success": True, "message": "Bot started"})
    
    elif action == "stop":
        monitor.update_status("stopped")
        monitor.log_activity("control", {"action": "stopped_via_ui"})
        return jsonify({"success": True, "message": "Bot stopped"})
    
    elif action == "pause":
        monitor.update_status("paused")
        monitor.log_activity("control", {"action": "paused_via_ui"})
        return jsonify({"success": True, "message": "Bot paused"})
    
    else:
        return jsonify({"success": False, "message": "Unknown action"}), 400


def create_templates():
    """Create HTML templates for the UI."""
    import os
    
    # Create templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), '../templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit Bot Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
        }
        
        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-running { background-color: #d4edda; color: #155724; }
        .status-stopped { background-color: #f8d7da; color: #721c24; }
        .status-paused { background-color: #fff3cd; color: #856404; }
        .status-error { background-color: #f8d7da; color: #721c24; }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .stat-item {
            text-align: center;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
            color: #333;
            cursor: pointer;
            font-size: 14px;
        }
        
        .btn:hover {
            background-color: #f8f9fa;
        }
        
        .btn-start { border-color: #28a745; color: #28a745; }
        .btn-stop { border-color: #dc3545; color: #dc3545; }
        .btn-pause { border-color: #ffc107; color: #856404; }
        
        .activity-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .activity-item {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }
        
        .activity-time {
            color: #6c757d;
            font-size: 12px;
        }
        
        .activity-type {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .error-item {
            padding: 10px;
            margin-bottom: 10px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            color: #721c24;
            font-size: 14px;
        }
        
        .info-list {
            list-style: none;
            padding: 0;
        }
        
        .info-list li {
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        .info-list li:last-child {
            border-bottom: none;
        }
        
        .refresh-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .stat-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <button class="refresh-btn" onclick="refreshData()">Refresh</button>
    
    <div class="container">
        <div class="header">
            <h1>Reddit Bot Monitor</h1>
            <span id="status-badge" class="status-badge">Loading...</span>
            <div style="margin-top: 10px;">
                <strong>Uptime:</strong> <span id="uptime">--</span> |
                <strong>Last Activity:</strong> <span id="last-activity">--</span>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Statistics</h3>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="posts-checked">0</div>
                        <div class="stat-label">Posts Checked</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="responses-generated">0</div>
                        <div class="stat-label">Responses Generated</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="successful-replies">0</div>
                        <div class="stat-label">Successful Replies</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="keywords-matched">0</div>
                        <div class="stat-label">Keywords Matched</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Controls</h3>
                <div class="controls">
                    <button class="btn btn-start" onclick="controlBot('start')">Start</button>
                    <button class="btn btn-pause" onclick="controlBot('pause')">Pause</button>
                    <button class="btn btn-stop" onclick="controlBot('stop')">Stop</button>
                </div>
                
                <h4>Configuration</h4>
                <ul class="info-list">
                    <li><strong>Subreddits:</strong> <span id="subreddits">--</span></li>
                    <li><strong>LLM Providers:</strong> <span id="providers">--</span></li>
                </ul>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Recent Activity</h3>
                <div class="activity-list" id="activity-list">
                    <div class="activity-item">Loading...</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Errors</h3>
                <div id="error-list">
                    <div class="activity-item">No errors</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchData(endpoint) {
            try {
                const response = await fetch(`/api/${endpoint}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }
        
        async function updateStatus() {
            const data = await fetchData('status');
            if (!data) return;
            
            const statusBadge = document.getElementById('status-badge');
            statusBadge.textContent = data.status;
            statusBadge.className = `status-badge status-${data.status}`;
            
            document.getElementById('uptime').textContent = data.uptime || '--';
            document.getElementById('last-activity').textContent = 
                data.last_activity ? new Date(data.last_activity).toLocaleString() : '--';
            
            // Update stats
            document.getElementById('posts-checked').textContent = data.stats.posts_checked;
            document.getElementById('responses-generated').textContent = data.stats.responses_generated;
            document.getElementById('successful-replies').textContent = data.stats.successful_replies;
            document.getElementById('keywords-matched').textContent = data.stats.keywords_matched;
            
            // Update config
            document.getElementById('subreddits').textContent = data.subreddits.join(', ');
            document.getElementById('providers').textContent = data.providers.join(', ') || 'None';
        }
        
        async function updateActivity() {
            const data = await fetchData('activity');
            if (!data) return;
            
            const activityList = document.getElementById('activity-list');
            if (data.activities.length === 0) {
                activityList.innerHTML = '<div class="activity-item">No recent activity</div>';
                return;
            }
            
            activityList.innerHTML = data.activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-time">${new Date(activity.timestamp).toLocaleString()}</div>
                    <div class="activity-type">${activity.type}</div>
                    <div>${JSON.stringify(activity.details)}</div>
                </div>
            `).join('');
        }
        
        async function updateErrors() {
            const data = await fetchData('errors');
            if (!data) return;
            
            const errorList = document.getElementById('error-list');
            if (data.errors.length === 0) {
                errorList.innerHTML = '<div class="activity-item">No recent errors</div>';
                return;
            }
            
            errorList.innerHTML = data.errors.map(error => `
                <div class="error-item">
                    <div class="activity-time">${new Date(error.timestamp).toLocaleString()}</div>
                    <div>${error.message}</div>
                </div>
            `).join('');
        }
        
        async function controlBot(action) {
            try {
                const response = await fetch(`/api/control/${action}`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    await refreshData();
                } else {
                    alert(`Error: ${result.message}`);
                }
            } catch (error) {
                console.error(`Error controlling bot:`, error);
                alert('Error communicating with bot');
            }
        }
        
        async function refreshData() {
            await Promise.all([
                updateStatus(),
                updateActivity(),
                updateErrors()
            ]);
        }
        
        // Initial load and auto-refresh
        refreshData();
        setInterval(refreshData, 5000); // Refresh every 5 seconds
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write(dashboard_html)


def run_ui(host='localhost', port=5000, debug=False):
    """Run the monitoring UI."""
    create_templates()
    logger.info(f"Starting monitoring UI on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


# Export the monitor instance for use by the main bot
__all__ = ['monitor', 'run_ui', 'app']