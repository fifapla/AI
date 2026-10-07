import sys
import json
import datetime
import platform
import psutil

def get_system_metrics():
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "ram_usage_percent": psutil.virtual_memory().percent,
        "timestamp": datetime.datetime.now().isoformat()
    }

def handle_request(request_json):
    try:
        req = json.loads(request_json)
        method = req.get("method")
        req_id = req.get("id")

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_system_metrics",
                            "description": "Returns current CPU, RAM and OS information for Windows host.",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                }
            }
        elif method == "tools/call":
            params = req.get("params", {})
            if params.get("name") == "get_system_metrics":
                metrics = get_system_metrics()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(metrics, indent=2)}]
                    }
                }
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}

if __name__ == "__main__":
    # Standard I/O loop for MCP
    for line in sys.stdin:
        if line.strip():
            response = handle_request(line.strip())
            print(json.dumps(response), flush=True)