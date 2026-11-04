"""Sync (no-asyncio) localhost sender for Isaac Sim python_server.

Same wire protocol as isaacsim_send.py raw mode: send source bytes,
shutdown(SHUT_WR), read-all, parse JSON. Avoids asyncio (whose proactor
self-pipe is blocked in sandboxed shells).
"""
import json
import socket
import sys

host, port, timeout, path = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
with open(path) as f:
    source = f.read()
indented = "\n".join("    " + line for line in source.splitlines())
payload = "async def _isolated_script():\n" + indented + "\n\nawait _isolated_script()"

s = socket.create_connection((host, port), timeout=timeout)
s.settimeout(timeout)
s.sendall(payload.encode())
s.shutdown(socket.SHUT_WR)
chunks = []
while True:
    b = s.recv(65536)
    if not b:
        break
    chunks.append(b)
s.close()
data = b"".join(chunks).decode()
result = json.loads(data)
print(json.dumps(result, indent=2))
sys.exit(0 if result.get("status") == "ok" else 1)
