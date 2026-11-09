"""Shared helpers: stdlib only, no account, no API key."""
import json, time, urllib.request

UA = {"User-Agent": "semilla1-near-thesis/1.0", "Content-Type": "application/json"}
ARCHIVAL = "https://archival-rpc.mainnet.fastnear.com"   # public, free (docs.near.org/api/rpc/providers)

def get_json(url, timeout=40, tries=4):
    last = None
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))
        except Exception as e:
            last = e; time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET {url} failed: {last}")

def rpc(method, params, url=ARCHIVAL, tries=5):
    """Returns (result, error). error is the RPC error dict (e.g. UNKNOWN_BLOCK for a skipped height)."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for i in range(tries):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, body, UA), timeout=30))
            if "result" in d:
                return d["result"], None
            err = d.get("error", {})
            name = (err.get("cause") or {}).get("name") or err.get("name")
            if name in ("UNKNOWN_BLOCK", "UNKNOWN_CHUNK"):
                return None, err
            last = err
        except Exception as e:
            last = e
        time.sleep(1.5 * (i + 1))
    return None, {"name": "RPC_FAILED", "detail": str(last)}
