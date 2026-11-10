#!/usr/bin/env python3
"""SBTC genesis block offline computation, replicating Bitcoin Core CreateGenesisBlock."""
import hashlib, struct, json

def dsha(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()

psz = b"2026-11-10 SBTC genesis - a Bitcoin-compatible chain"
# scriptSig = CScript() << 486604799 << CScriptNum(4) << psz
# 486604799 = 0x1d00ffff -> CScriptNum bytes ff ff 00 1d, pushed as 4-byte data: 04 ffffff001d.. (LE bytes: ff ff 00 1d)
script_sig = b"\x04\xff\xff\x00\x1d" + b"\x01\x04" + bytes([len(psz)]) + psz
pubkey = bytes.fromhex("04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f")
script_pub = bytes([len(pubkey)]) + pubkey + b"\xac"

def varint(n):
    if n < 0xfd: return bytes([n])
    if n <= 0xffff: return b"\xfd" + struct.pack("<H", n)
    return b"\xfe" + struct.pack("<I", n)

tx = struct.pack("<i", 1)
tx += varint(1)
tx += b"\x00"*32 + struct.pack("<I", 0xffffffff)
tx += varint(len(script_sig)) + script_sig
tx += struct.pack("<I", 0xffffffff)
tx += varint(1)
tx += struct.pack("<q", 50*100_000_000)
tx += varint(len(script_pub)) + script_pub
tx += struct.pack("<I", 0)

txid_internal = dsha(tx)
merkle = txid_internal  # single tx
print("coinbase tx hex:", tx.hex())
print("txid/merkle (display):", txid_internal[::-1].hex())

nTime = 1794268800  # 2026-11-10 00:00:00 UTC, verified: date -d "2026-11-10 UTC" +%s
nBits = 0x207fffff
# target from compact
exp = nBits >> 24
mant = nBits & 0x7fffff
target = mant * 256**(exp-3)
nonce = 0
while True:
    header = struct.pack("<i", 1) + b"\x00"*32 + merkle + struct.pack("<I", nTime) + struct.pack("<I", nBits) + struct.pack("<I", nonce)
    h = dsha(header)
    if int.from_bytes(h[::-1], "big") <= target:
        print("nTime:", nTime, "nBits: 0x%08x" % nBits, "nonce:", nonce)
        print("genesis hash (display):", h[::-1].hex())
        print(json.dumps({"nTime": nTime, "nNonce": nonce, "nBits": hex(nBits),
                          "hash": h[::-1].hex(), "merkle": txid_internal[::-1].hex()}))
        break
    nonce += 1
