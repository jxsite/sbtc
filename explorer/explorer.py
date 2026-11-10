#!/usr/bin/env python3
"""SBTC block explorer - zero-dependency (Python stdlib only).

Talks to a local sbtcd over JSON-RPC on 127.0.0.1. RPC credentials are read
at runtime from the node's sbtc.conf (or .cookie fallback) and are never
logged or rendered. Bind loopback only; a reverse proxy / tunnel decides
if and how this becomes public.
"""
import base64
import html
import http.client
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

DATADIR = os.environ.get("SBTC_DATADIR", "/home/ubuntu/.sbtc-seed")
CONF = os.environ.get("SBTC_RPC_CONF", os.path.join(DATADIR, "sbtc.conf"))
HOST = os.environ.get("SBTC_EXPLORER_HOST", "127.0.0.1")
PORT = int(os.environ.get("SBTC_EXPLORER_PORT", "3002"))
HISTORY_FULL_SCAN_MAX = 5000  # blocks; beyond this, address history is partial

# Stage 5: download page + faucet. The faucet spends from a dedicated wallet
# on the node (default name "faucet"); it only pays out when that wallet has
# confirmed (trusted) balance, so an unfunded faucet honestly reports
# "not open yet" instead of faking success.
FAUCET_WALLET = os.environ.get("SBTC_FAUCET_WALLET", "faucet")
FAUCET_AMOUNT = float(os.environ.get("SBTC_FAUCET_AMOUNT", "1"))
FAUCET_COOLDOWN = int(os.environ.get("SBTC_FAUCET_COOLDOWN_HOURS", "24")) * 3600
FAUCET_FEE_RESERVE = 0.01  # keep this much aside for the payout tx fee
FAUCET_STATE = os.environ.get("SBTC_FAUCET_STATE",
                              "/home/ubuntu/sbtc-explorer/faucet_state.json")
DOWNLOAD_DIR = os.environ.get("SBTC_DOWNLOAD_DIR",
                              "/home/ubuntu/sbtc-explorer/downloads")
DOWNLOAD_FILES = {  # url name -> (filename in DOWNLOAD_DIR, content type)
    "SBTC-Windows-v1.zip": ("SBTC-Windows-v1.zip", "application/zip"),
    "sbtc-qt-linux": ("sbtc-qt-linux", "application/octet-stream"),
}

_scan_lock = threading.Lock()
_cache_lock = threading.Lock()
_info_cache = {"t": 0.0, "v": None}
_block_cache = {}  # hash -> block (verbosity 2/3 results are immutable)


def load_rpc_auth():
    user = password = None
    port = 29332
    try:
        with open(CONF, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k == "rpcuser":
                    user = v
                elif k == "rpcpassword":
                    password = v
                elif k == "rpcport":
                    port = int(v)
    except FileNotFoundError:
        pass
    if not user or not password:
        cookie = os.path.join(DATADIR, ".cookie")
        with open(cookie, "r", encoding="utf-8") as f:
            user, password = f.read().strip().split(":", 1)
    return user, password, port


RPC_USER, RPC_PASS, RPC_PORT = load_rpc_auth()
_AUTH = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()


def _rpc_once(method, params, timeout, path, auth):
    body = json.dumps({"jsonrpc": "1.0", "id": "explorer",
                       "method": method, "params": params}).encode()
    conn = http.client.HTTPConnection("127.0.0.1", RPC_PORT, timeout=timeout)
    try:
        conn.request("POST", path, body,
                     {"Authorization": f"Basic {auth}",
                      "Content-Type": "application/json"})
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        return resp.status, raw
    finally:
        conn.close()


def rpc(method, params=None, timeout=30, wallet=None):
    global _AUTH
    path = f"/wallet/{wallet}" if wallet else "/"
    status, raw = _rpc_once(method, params or [], timeout, path, _AUTH)
    if status == 401:
        # Node restarted -> cookie auth rotated. Reload credentials once
        # (conf rpcuser/rpcpassword or .cookie) and retry before failing.
        user, password, _ = load_rpc_auth()
        _AUTH = base64.b64encode(f"{user}:{password}".encode()).decode()
        status, raw = _rpc_once(method, params or [], timeout, path, _AUTH)
    data = json.loads(raw)
    if data.get("error"):
        raise RpcError(method, data["error"].get("message", "rpc error"))
    return data["result"]


class RpcError(Exception):
    def __init__(self, method, msg):
        super().__init__(f"{method}: {msg}")
        self.method = method
        self.msg = msg


def chain_info():
    with _cache_lock:
        if time.time() - _info_cache["t"] < 3 and _info_cache["v"]:
            return _info_cache["v"]
    v = rpc("getblockchaininfo")
    with _cache_lock:
        _info_cache.update(t=time.time(), v=v)
    return v


def get_block(hash_or_height, verbosity=2):
    if isinstance(hash_or_height, int) or str(hash_or_height).isdigit():
        h = rpc("getblockhash", [int(hash_or_height)])
    else:
        h = str(hash_or_height)
    key = (h, verbosity)
    with _cache_lock:
        if key in _block_cache:
            return _block_cache[key]
    b = rpc("getblock", [h, verbosity], timeout=60)
    with _cache_lock:
        if len(_block_cache) < 2000:
            _block_cache[key] = b
    return b


def fmt_time(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(int(ts)))


def fmt_amt(v):
    return f"{float(v):.8f}".rstrip("0").rstrip(".") if float(v) else "0"


def short(h, n=16):
    h = str(h)
    return h if len(h) <= n else h[:n] + "…"


def layout(title, body):
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · SBTC Explorer</title>
<style>
body{{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;background:#0f1420;color:#dbe4f0}}
header{{background:#16203a;padding:14px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
header a.logo{{color:#f5b942;font-weight:700;font-size:20px;text-decoration:none}}
header form{{flex:1;min-width:240px}} header input{{width:100%;padding:8px 10px;border-radius:6px;border:1px solid #33415e;background:#0f1420;color:#fff}}
main{{max-width:1000px;margin:0 auto;padding:20px}}
.card{{background:#182238;border:1px solid #27355a;border-radius:10px;padding:16px 20px;margin-bottom:18px}}
h2{{margin:4px 0 12px;font-size:18px;color:#f5b942}} a{{color:#6cb2f5;text-decoration:none}} a:hover{{text-decoration:underline}}
table{{width:100%;border-collapse:collapse;font-size:14px}} td,th{{padding:7px 8px;border-bottom:1px solid #27355a;text-align:left;vertical-align:top}}
.mono{{font-family:ui-monospace,Menlo,Consolas,monospace;word-break:break-all;font-size:13px}}
.mut{{color:#8fa3c0}} .err{{color:#ff7b72}} footer{{text-align:center;color:#5f7191;padding:18px;font-size:12px}}
</style></head><body>
<header><a class="logo" href="/">SBTC Explorer</a>
<a href="/download" style="color:#dbe4f0;font-size:14px">钱包下载</a>
<a href="/faucet" style="color:#dbe4f0;font-size:14px">水龙头领币</a>
<form action="/search" method="get"><input name="q" placeholder="搜索：块高度 / 块哈希 / 交易ID / 地址"></form></header>
<main>{body}</main><footer>SBTC · Bitcoin-compatible chain · 数据来自本地节点 RPC</footer></body></html>"""


def kv_table(rows):
    trs = "".join(f"<tr><td class='mut' style='width:180px'>{k}</td><td>{v}</td></tr>" for k, v in rows)
    return f"<table>{trs}</table>"


def home_page():
    info = chain_info()
    tip = int(info["blocks"])
    rows = [
        ("当前高度", f"<b>{tip}</b>"),
        ("最新块哈希", f"<a class='mono' href='/block/{info['bestblockhash']}'>{info['bestblockhash']}</a>"),
        ("难度", f"{info['difficulty']:.10g}"),
        ("最新块时间", fmt_time(info["time"])),
        ("链上数据大小", f"{info['size_on_disk']} bytes"),
    ]
    blocks = []
    for h in range(tip, max(tip - 15, -1), -1):
        b = get_block(h, 1)
        blocks.append(f"<tr><td><a href='/block/{b['hash']}'>{b['height']}</a></td>"
                      f"<td class='mono'><a href='/block/{b['hash']}'>{short(b['hash'], 24)}</a></td>"
                      f"<td>{fmt_time(b['time'])}</td><td>{b['nTx']}</td><td>{b['size']}</td></tr>")
    body = (f"<div class='card'><h2>开始使用 SBTC</h2><p>"
            f"<a href='/download'><b>下载钱包 / 挖矿包</b></a>（Windows 一键包，解压即用）"
            f"　·　<a href='/faucet'><b>水龙头领币</b></a>（免费领 SBTC 体验）</p></div>"
            f"<div class='card'><h2>链概况 · SBTC</h2>{kv_table(rows)}</div>"
            f"<div class='card'><h2>最新区块</h2><table><tr><th>高度</th><th>哈希</th><th>时间</th><th>交易数</th><th>大小(B)</th></tr>"
            + "".join(blocks) + "</table></div>")
    return layout("首页", body)


def block_page(ident):
    b = get_block(ident, 2)
    rows = [
        ("块哈希", f"<span class='mono'>{b['hash']}</span>"),
        ("高度", str(b["height"])),
        ("确认数", str(b.get("confirmations", ""))),
        ("时间", fmt_time(b["time"])),
        ("交易数", str(b["nTx"])),
        ("大小 / 重量", f"{b['size']} B / {b['weight']} WU"),
        ("Merkle Root", f"<span class='mono'>{b['merkleroot']}</span>"),
        ("Nonce", str(b["nonce"])),
        ("Bits", f"<span class='mono'>{b['bits']}</span>"),
        ("难度", f"{b['difficulty']:.10g}"),
    ]
    if b.get("previousblockhash"):
        rows.append(("上一块", f"<a class='mono' href='/block/{b['previousblockhash']}'>{b['previousblockhash']}</a>"))
    if b.get("nextblockhash"):
        rows.append(("下一块", f"<a class='mono' href='/block/{b['nextblockhash']}'>{b['nextblockhash']}</a>"))
    txrows = []
    for tx in b["tx"]:
        total = sum(float(o.get("value", 0)) for o in tx.get("vout", []))
        txrows.append(f"<tr><td class='mono'><a href='/tx/{tx['txid']}'>{short(tx['txid'], 32)}</a></td>"
                      f"<td>{len(tx.get('vin', []))} in / {len(tx.get('vout', []))} out</td><td>{fmt_amt(total)} SBTC</td></tr>")
    body = (f"<div class='card'><h2>区块 #{b['height']}</h2>{kv_table(rows)}</div>"
            f"<div class='card'><h2>交易（{b['nTx']}）</h2><table><tr><th>交易ID</th><th>输入/输出</th><th>输出合计</th></tr>"
            + "".join(txrows) + "</table></div>")
    return layout(f"区块 #{b['height']}", body)


def find_tx(txid):
    """Return (tx, block_hash_or_None, height_or_None). getrawtransaction
    without txindex only covers mempool/wallet txs, so fall back to a
    block scan (chain is small; results cached per block)."""
    try:
        tx = rpc("getrawtransaction", [txid, True])
        bh, height = tx.get("blockhash"), None
        if bh:
            try:
                height = get_block(bh, 1)["height"]
            except RpcError:
                pass
        return tx, bh, height
    except RpcError:
        pass
    tip = int(chain_info()["blocks"])
    for h in range(tip, -1, -1):
        b = get_block(h, 3)
        for tx in b["tx"]:
            if tx["txid"] == txid:
                tx = dict(tx)
                tx["blockhash"] = b["hash"]
                tx["blocktime"] = b["time"]
                tx["confirmations"] = tip - h + 1
                return tx, b["hash"], h
    raise RpcError("getrawtransaction", "transaction not found")


def script_addr(spk):
    if not spk:
        return None
    if spk.get("address"):
        return spk["address"]
    addrs = spk.get("addresses") or []
    return addrs[0] if addrs else None


def addr_link(a):
    return f"<a class='mono' href='/address/{quote(a)}'>{html.escape(a)}</a>" if a else "<span class='mut'>(无地址，如 OP_RETURN/裸公钥)</span>"


def tx_page(txid):
    tx, bh, height = find_tx(txid)
    in_total = out_total = 0.0
    vin_rows = []
    for vin in tx.get("vin", []):
        if "coinbase" in vin:
            raw = bytes.fromhex(vin["coinbase"])
            txt = "".join(chr(c) if 32 <= c < 127 else " " for c in raw)
            vin_rows.append(f"<tr><td colspan='2'>Coinbase（新币发行）<div class='mono mut'>{html.escape(txt.strip())}</div></td></tr>")
        else:
            pv = vin.get("prevout") or {}
            val = float(pv.get("value", 0))
            in_total += val
            vin_rows.append(f"<tr><td class='mono'><a href='/tx/{vin.get('txid','')}'>{short(vin.get('txid',''), 24)}</a>:{vin.get('vout','')}</td>"
                            f"<td>{addr_link(script_addr(pv.get('scriptPubKey')))}<br>{fmt_amt(val)} SBTC</td></tr>")
    vout_rows = []
    for o in tx.get("vout", []):
        val = float(o.get("value", 0))
        out_total += val
        vout_rows.append(f"<tr><td>#{o.get('n')}</td><td>{addr_link(script_addr(o.get('scriptPubKey')))}</td><td>{fmt_amt(val)} SBTC</td></tr>")
    rows = [
        ("交易ID", f"<span class='mono'>{tx['txid']}</span>"),
        ("状态", f"{tx.get('confirmations', 0)} 个确认" if tx.get("confirmations") else "未确认（内存池）"),
        ("所在块", f"<a class='mono' href='/block/{bh}'>{bh}</a>（高度 {height}）" if bh else "—"),
        ("时间", fmt_time(tx["blocktime"]) if tx.get("blocktime") else "—"),
        ("大小 / 虚拟大小", f"{tx.get('size','')} / {tx.get('vsize','')}"),
    ]
    if in_total:
        rows.append(("手续费", f"{fmt_amt(in_total - out_total)} SBTC"))
    body = (f"<div class='card'><h2>交易详情</h2>{kv_table(rows)}</div>"
            f"<div class='card'><h2>输入</h2><table>{''.join(vin_rows) or '<tr><td>无</td></tr>'}</table></div>"
            f"<div class='card'><h2>输出</h2><table><tr><th>#</th><th>地址</th><th>金额</th></tr>{''.join(vout_rows)}</table></div>")
    return layout("交易详情", body)


ADDR_RE = re.compile(r"^[a-zA-Z0-9]{20,80}$")


def address_page(addr):
    if not ADDR_RE.match(addr or "") or not (addr.startswith("sbtc1") or addr[0] in "Ss"):
        return layout("地址无效", "<div class='card'><h2 class='err'>地址格式无效</h2>"
                                  "<p class='mut'>只接受 SBTC 地址（sbtc1… / S… / s…）。</p></div>"), 400
    with _scan_lock:
        scan = rpc("scantxoutset", ["start", [f"addr({addr})"]], timeout=120)
    tip = int(chain_info()["blocks"])
    full = tip <= HISTORY_FULL_SCAN_MAX
    hist = []
    total_in = total_out = 0.0
    for h in range(tip, -1, -1) if full else range(tip, max(tip - HISTORY_FULL_SCAN_MAX, -1), -1):
        b = get_block(h, 3)
        for tx in b["tx"]:
            rec = sum(float(o["value"]) for o in tx.get("vout", []) if script_addr(o.get("scriptPubKey")) == addr)
            sent = sum(float(v["prevout"]["value"]) for v in tx.get("vin", [])
                       if v.get("prevout") and script_addr(v["prevout"].get("scriptPubKey")) == addr)
            if rec or sent:
                hist.append((tx["txid"], h, b["time"], rec, sent))
                total_in += rec
                total_out += sent
    hrows = "".join(
        f"<tr><td class='mono'><a href='/tx/{t}'>{short(t, 24)}</a></td><td><a href='/block/{hh}'>{hh}</a></td>"
        f"<td>{fmt_time(ts)}</td><td>+{fmt_amt(r)}</td><td>-{fmt_amt(s)}</td><td>{fmt_amt(r - s)}</td></tr>"
        for t, hh, ts, r, s in hist)
    urows = "".join(
        f"<tr><td class='mono'><a href='/tx/{u['txid']}'>{short(u['txid'], 24)}</a>:{u['vout']}</td><td>{fmt_amt(u['amount'])} SBTC</td></tr>"
        for u in scan.get("unspents", []))
    note = "" if full else f"<p class='mut'>链高已超过 {HISTORY_FULL_SCAN_MAX} 块，交易历史仅显示最近部分；余额（UTXO 扫描）仍为全量准确值。</p>"
    rows = [
        ("地址", f"<span class='mono'>{html.escape(addr)}</span>"),
        ("当前余额", f"<b>{fmt_amt(scan['total_amount'])} SBTC</b>（UTXO {scan['txouts']} 个，扫描高度 {scan['height']}）"),
        ("历史总收入", f"{fmt_amt(total_in)} SBTC"),
        ("历史总支出", f"{fmt_amt(total_out)} SBTC"),
        ("历史交易数", str(len(hist))),
    ]
    body = (f"<div class='card'><h2>地址</h2>{kv_table(rows)}{note}</div>"
            f"<div class='card'><h2>未花费输出（UTXO）</h2><table><tr><th>来源交易</th><th>金额</th></tr>{urows or '<tr><td class=mut>无</td></tr>'}</table></div>"
            f"<div class='card'><h2>交易历史</h2><table><tr><th>交易ID</th><th>块高</th><th>时间</th><th>收入</th><th>支出</th><th>净变动</th></tr>{hrows or '<tr><td class=mut>无记录</td></tr>'}</table></div>")
    return layout("地址详情", body)


# ---------------- stage 5: downloads + faucet ----------------

_faucet_lock = threading.Lock()


def _faucet_state_load():
    try:
        with open(FAUCET_STATE, "r", encoding="utf-8") as f:
            st = json.load(f)
    except Exception:  # noqa: BLE001 - missing/corrupt state = fresh start
        st = {}
    st.setdefault("claims", [])
    return st


def _faucet_state_save(st):
    tmp = FAUCET_STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, FAUCET_STATE)


def faucet_balances():
    """getbalances()['mine'] of the faucet wallet, loading it if needed.
    Returns None when the wallet does not exist / cannot be loaded."""
    try:
        if FAUCET_WALLET not in rpc("listwallets"):
            try:
                rpc("loadwallet", [FAUCET_WALLET])
            except RpcError:
                return None
        return rpc("getbalances", wallet=FAUCET_WALLET)["mine"]
    except RpcError:
        return None


def faucet_funding_address():
    st = _faucet_state_load()
    if st.get("address"):
        return st["address"]
    addr = rpc("getnewaddress", ["faucet"], wallet=FAUCET_WALLET)
    st["address"] = addr
    _faucet_state_save(st)
    return addr


def faucet_status():
    """-> (state, balances) where state in open|unfunded|confirming|nowallet."""
    bal = faucet_balances()
    if bal is None:
        return "nowallet", None
    trusted = float(bal.get("trusted", 0))
    pending = float(bal.get("untrusted_pending", 0)) + float(bal.get("immature", 0))
    if trusted >= FAUCET_AMOUNT + FAUCET_FEE_RESERVE:
        return "open", bal
    if pending > 0:
        return "confirming", bal
    return "unfunded", bal


def faucet_claim(addr, ip):
    """Attempt a payout. Returns (ok, message_html). All checks and the send
    itself happen under one lock so the balance cannot be double-spent by
    concurrent claims."""
    with _faucet_lock:
        if not addr or not ADDR_RE.match(addr) or not (addr.startswith("sbtc1") or addr[0] in "Ss"):
            return False, "地址格式无效，只接受 SBTC 地址（sbtc1… / S… / s…）。"
        try:
            va = rpc("validateaddress", [addr])
        except RpcError as e:
            return False, f"地址校验失败：{html.escape(e.msg)}"
        if not va.get("isvalid"):
            return False, "这不是一个有效的 SBTC 地址，请检查后重试。"
        st = _faucet_state_load()
        now = time.time()
        for c in st["claims"]:
            if now - float(c.get("t", 0)) < FAUCET_COOLDOWN and (c.get("addr") == addr or c.get("ip") == ip):
                return False, (f"领取太频繁：每个地址 / 每个 IP 每 "
                               f"{FAUCET_COOLDOWN // 3600} 小时只能领 1 次，请稍后再来。")
        state, bal = faucet_status()
        if state != "open":
            return False, ("水龙头暂未开放：水龙头钱包还没有可用余额。"
                           "等有人往水龙头地址注资并确认后会自动开放，请稍后再来。")
        try:
            txid = rpc("sendtoaddress", [addr, FAUCET_AMOUNT], wallet=FAUCET_WALLET)
        except RpcError as e:
            return False, f"发放失败：{html.escape(e.msg)}"
        st["claims"].append({"addr": addr, "ip": ip, "txid": txid,
                             "t": now, "amount": FAUCET_AMOUNT})
        _faucet_state_save(st)
        return True, (f"已发放 {fmt_amt(FAUCET_AMOUNT)} SBTC！交易ID："
                      f"<a class='mono' href='/tx/{txid}'>{txid}</a><br>"
                      f"<span class='mut'>交易已广播，等下一个块确认后到账（挖矿出块后）。</span>")


def download_page():
    def size_of(url_name):
        fn, _ = DOWNLOAD_FILES[url_name]
        p = os.path.join(DOWNLOAD_DIR, fn)
        return (f"{os.path.getsize(p) / 1048576:.1f} MB" if os.path.exists(p)
                else "（文件准备中）")
    body = f"""<div class='card'><h2>SBTC 是什么</h2>
<p>SBTC 是一条复刻比特币规则的独立区块链：总量 2100 万、出块奖励 50 个起、每 21 万块减半，
普通电脑 CPU 就能挖矿。</p></div>
<div class='card'><h2>Windows 钱包 + 一键挖矿包</h2>
<p>解压即用：图形钱包、节点、挖矿脚本全套。双击「1-打开钱包」看钱包，
双击「2-开始挖矿」开始挖矿。</p>
<p><a href='/download/SBTC-Windows-v1.zip'><b>下载 SBTC-Windows-v1.zip</b></a>
<span class='mut'>（{size_of('SBTC-Windows-v1.zip')}）</span></p>
<p class='mut'>注意：节点同步需要种子节点端口对外开放；钱包文件请自行备份（包内 README 有说明）。</p></div>
<div class='card'><h2>Linux 钱包</h2>
<p><a href='/download/sbtc-qt-linux'><b>下载 sbtc-qt（Linux 图形钱包）</b></a>
<span class='mut'>（{size_of('sbtc-qt-linux')}，Ubuntu 24.04 构建，chmod +x 后运行）</span></p>
<p class='mut'>Linux 命令行版（sbtcd / sbtc-cli）与完整源码将在 GitHub 发布页提供。</p></div>
<div class='card'><h2>其他入口</h2>
<p><a href='/'>区块浏览器首页</a>（查块、查交易、查地址）　·　<a href='/faucet'>水龙头领币</a></p></div>"""
    return layout("钱包下载", body)


def faucet_page(msg=None, ok=None):
    state, bal = faucet_status()
    try:
        fund_addr = faucet_funding_address()
    except RpcError:
        fund_addr = None
    if state == "open":
        status = (f"<p>状态：<b>已开放</b>，水龙头余额 "
                  f"<b>{fmt_amt(bal.get('trusted', 0))} SBTC</b>，每次可领 "
                  f"<b>{fmt_amt(FAUCET_AMOUNT)} SBTC</b>。</p>")
        form = (f"<form action='/faucet/claim' method='post'>"
                f"<input name='address' placeholder='粘贴你的 SBTC 地址（sbtc1…）' "
                f"style='width:100%;padding:8px 10px;border-radius:6px;border:1px solid #33415e;background:#0f1420;color:#fff'>"
                f"<p><button type='submit' style='padding:9px 22px;border:0;border-radius:6px;background:#f5b942;color:#111;font-weight:700;cursor:pointer'>领取 {fmt_amt(FAUCET_AMOUNT)} SBTC</button></p></form>")
    elif state == "confirming":
        status = ("<p>状态：<b>注资确认中</b>——已经有人往水龙头转了币，"
                  "等确认到账后自动开放领取。</p>")
        form = ""
    elif state == "unfunded":
        status = ("<p>状态：<b>水龙头待注资，暂未开放领取</b>。"
                  "往下面这个水龙头地址转入 SBTC 并确认后，领取会自动开放。</p>")
        form = ""
    else:
        status = "<p>状态：<b>水龙头钱包尚未就绪，暂未开放</b>。</p>"
        form = ""
    msg_html = ""
    if msg:
        cls = "" if ok else " class='err'"
        msg_html = f"<div class='card'><p{cls}>{msg}</p></div>"
    fund = (f"<div class='card'><h2>给水龙头注资</h2>"
            f"<p class='mut'>水龙头收款地址（往这里转 SBTC 就能让大家领币）：</p>"
            f"<p class='mono'>{html.escape(fund_addr)}</p></div>") if fund_addr else ""
    body = (f"<div class='card'><h2>SBTC 水龙头（免费领币）</h2>{status}"
            f"<p class='mut'>规则：每次领 {fmt_amt(FAUCET_AMOUNT)} SBTC，每个地址 / 每个 IP 每 "
            f"{FAUCET_COOLDOWN // 3600} 小时限领 1 次。领到的币等下一个块确认后到账。</p>{form}</div>"
            f"{msg_html}{fund}")
    return layout("水龙头", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "SBTCExplorer/1.0"

    def log_message(self, fmt, *args):  # keep journal clean, no auth ever logged
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send(self, content, status=200):
        if isinstance(content, tuple):
            content, status = content
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        try:
            p = urlparse(self.path)
            path = p.path.rstrip("/") or "/"
            if path == "/":
                self._send(home_page())
            elif path == "/healthz":
                info = chain_info()
                self._send(f"ok height={info['blocks']}")
            elif path == "/search":
                q = (parse_qs(p.query).get("q") or [""])[0].strip()
                self._redirect_for_query(q)
            elif path.startswith("/block/"):
                self._send(block_page(path.split("/", 2)[2]))
            elif path.startswith("/tx/"):
                self._send(tx_page(path.split("/", 2)[2]))
            elif path.startswith("/address/"):
                self._send(address_page(path.split("/", 2)[2]))
            elif path == "/download":
                self._send(download_page())
            elif path.startswith("/download/"):
                name = path.split("/", 2)[2]
                if name not in DOWNLOAD_FILES:
                    self._send(layout("404", "<div class='card'><h2>404</h2><p class='mut'>文件不存在。</p></div>"), 404)
                else:
                    fn, ctype = DOWNLOAD_FILES[name]
                    self._send_file(os.path.join(DOWNLOAD_DIR, fn), ctype, fn)
            elif path == "/faucet":
                self._send(faucet_page())
            else:
                self._send(layout("404", "<div class='card'><h2>404</h2><p class='mut'>页面不存在。</p></div>"), 404)
        except RpcError as e:
            self._send(layout("查询失败", f"<div class='card'><h2 class='err'>查询失败</h2><p class='mono'>{html.escape(e.msg)}</p></div>"), 404)
        except Exception as e:  # noqa: BLE001
            self._send(layout("出错", f"<div class='card'><h2 class='err'>服务器出错</h2><p class='mono'>{html.escape(type(e).__name__)}</p></div>"), 500)

    def _send_file(self, fpath, ctype, fname):
        if not os.path.exists(fpath):
            self._send(layout("文件准备中",
                              "<div class='card'><h2>文件准备中</h2><p class='mut'>该下载文件尚未上传，请稍后再来。</p></div>"), 404)
            return
        size = os.path.getsize(fpath)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", f"attachment; filename={fname}")
        self.end_headers()
        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break

    def do_HEAD(self):
        p = urlparse(self.path)
        path = p.path.rstrip("/") or "/"
        if path.startswith("/download/"):
            name = path.split("/", 2)[2]
            if name in DOWNLOAD_FILES:
                fn, ctype = DOWNLOAD_FILES[name]
                fpath = os.path.join(DOWNLOAD_DIR, fn)
                if os.path.exists(fpath):
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(os.path.getsize(fpath)))
                    self.send_header("Content-Disposition", f"attachment; filename={fn}")
                    self.end_headers()
                    return
        self.send_response(404)
        self.end_headers()

    def _client_ip(self):
        xff = self.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        return self.client_address[0]

    def do_POST(self):
        try:
            p = urlparse(self.path)
            path = p.path.rstrip("/") or "/"
            if path == "/faucet/claim":
                n = int(self.headers.get("Content-Length", 0))
                form = parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
                addr = (form.get("address") or [""])[0].strip()
                ok, msg = faucet_claim(addr, self._client_ip())
                self._send(faucet_page(msg=msg, ok=ok))
            else:
                self._send(layout("404", "<div class='card'><h2>404</h2><p class='mut'>页面不存在。</p></div>"), 404)
        except Exception as e:  # noqa: BLE001
            self._send(layout("出错", f"<div class='card'><h2 class='err'>服务器出错</h2><p class='mono'>{html.escape(type(e).__name__)}</p></div>"), 500)

    def _redirect_for_query(self, q):
        if not q:
            loc = "/"
        elif q.isdigit():
            loc = f"/block/{q}"
        elif re.fullmatch(r"[0-9a-fA-F]{64}", q):
            try:
                rpc("getblock", [q, 0])
                loc = f"/block/{q}"
            except RpcError:
                loc = f"/tx/{q}"
        else:
            loc = f"/address/{quote(q)}"
        self.send_response(302)
        self.send_header("Location", loc)
        self.end_headers()


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SBTC explorer on http://{HOST}:{PORT} (rpc 127.0.0.1:{RPC_PORT})", flush=True)
    srv.serve_forever()
