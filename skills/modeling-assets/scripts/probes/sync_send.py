"""Sync (no-asyncio) localhost IPC sender for Isaac Sim python_server.

Same wire protocol as isaacsim_send.py --file (isolated wrap): TCP to
127.0.0.1:8226, send payload, SHUT_WR half-close, read-all, parse JSON.
Avoids asyncio's socketpair() self-pipe which is sandbox-blocked here.
Usage: python sync_send.py <probe.py> [timeout_s]
"""
import json
import socket
import sys

host = "127.0.0.1"
port = 8226
path = sys.argv[1]
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0

with open(path) as f:
    src = f.read()
indented = "\n".join("    " + line for line in src.splitlines())
payload = "async def _isolated_script():\n" + indented + "\n\nawait _isolated_script()"

s = socket.create_connection((host, port), timeout=timeout)
s.settimeout(timeout)
s.sendall(payload.encode())
s.shutdown(socket.SHUT_WR)
chunks = []
while True:
    d = s.recv(65536)
    if not d:
        break
    chunks.append(d)
s.close()
res = json.loads(b"".join(chunks).decode())
print(json.dumps(res, indent=2))
sys.exit(0 if res.get("status") == "ok" else 1)
