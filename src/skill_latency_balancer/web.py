import asyncio
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Skill Latency Balancer")

@dataclass
class NodeMetrics:
    node_id: str
    latency_ms: float
    load_factor: float
    active_tasks: int
    status: str

class NodeManager:
    def __init__(self):
        self.nodes: Dict[str, NodeMetrics] = {
            "node-alpha": NodeMetrics("node-alpha", 12.4, 0.45, 12, "healthy"),
            "node-beta": NodeMetrics("node-beta", 45.2, 0.88, 48, "warning"),
            "node-gamma": NodeMetrics("node-gamma", 8.1, 0.12, 3, "healthy"),
        }

    def get_all(self) -> List[dict]:
        return [asdict(n) for n in self.nodes.values()]

manager = NodeManager()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latency Balancer | Infrastructure</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = { darkMode: 'class', theme: { extend: { colors: { bg: '#09090B', card: '#121214', border: '#27272A' } } } }
    </script>
    <style>
        body { background-color: #09090B; color: #FAFAFA; font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-5xl mx-auto">
        <header class="mb-10">
            <h1 class="text-2xl font-semibold tracking-tight">Skill Latency Balancer</h1>
            <p class="text-zinc-500 text-sm mt-1">Real-time node telemetry and load distribution metrics.</p>
        </header>
        <div id="node-grid" class="grid grid-cols-1 md:grid-cols-3 gap-4"></div>
    </div>

    <script>
        const grid = document.getElementById('node-grid');
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            grid.innerHTML = data.map(node => `
                <div class="bg-card border border-border p-6 rounded-xl">
                    <div class="flex justify-between items-start mb-4">
                        <span class="font-mono text-sm font-bold">${node.node_id.toUpperCase()}</span>
                        <span class="px-2 py-0.5 rounded text-[10px] uppercase ${node.status === 'healthy' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}">${node.status}</span>
                    </div>
                    <div class="space-y-3">
                        <div class="flex justify-between text-sm"><span class="text-zinc-500">Latency</span><span class="font-mono">${node.latency_ms}ms</span></div>
                        <div class="flex justify-between text-sm"><span class="text-zinc-500">Load</span><span class="font-mono">${(node.load_factor * 100).toFixed(1)}%</span></div>
                        <div class="flex justify-between text-sm"><span class="text-zinc-500">Tasks</span><span class="font-mono">${node.active_tasks}</span></div>
                    </div>
                </div>
            `).join('');
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_TEMPLATE

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Simulate dynamic telemetry updates
            for node in manager.nodes.values():
                node.latency_ms = round(max(5.0, node.latency_ms + (time.time() % 2 - 1)), 2)
            
            await websocket.send_json(manager.get_all())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)