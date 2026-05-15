#!/usr/bin/env python3

import argparse
import os
import re
import sys
from impacket.smbconnection import SMBConnection
from colorama import Fore, init


init(autoreset=True)

INTERESTING_EXTENSIONS = [
    '.ps1', '.bat', '.cmd', '.vbs',       
    '.txt', '.log', '.md',                
    '.xml', '.json', '.yaml', '.yml',     
    '.config', '.conf', '.ini', '.env',   
    '.kdbx', '.kdb',                      
    '.pfx', '.pem', '.key', '.crt',      
    '.zip', '.tar', '.gz', '.7z',        
    '.xlsx', '.xls', '.csv',             
    '.docx', '.doc', '.pdf',             
    '.db', '.sqlite', '.sql',            
]

INTERESTING_KEYWORDS = [
    'password', 'passwd', 'pass', 'pwd',
    'secret', 'credential', 'cred',
    'backup', 'admin', 'root',
    'token', 'api', 'key',
    'hash', 'shadow', 'flag',
]

def print_banner():
    print(Fore.CYAN + r"""
   _____ __                   _____                                  
  / ___// /_  ____ _________ / ___/      _____  ___  ____  ___  _____
  \__ \/ __ \/ __ `/ ___/ _ \\__ \ | /| / / _ \/ _ \/ __ \/ _ \/ ___/
 ___/ / / / / /_/ / /  /  __/__/ / |/ |/ /  __/  __/ /_/ /  __/ /    
/____/_/ /_/\__,_/_/   \___/____/|__/|__/\___/\___/ .___/\___/_/     
                                                 /_/                  
""")
    print(Fore.WHITE + "SMB Share Recursive Enumerator\n")

def strip_colour(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def log(text, out=None):
    print(text)
    if out:
        out.write(strip_colour(text) + '\n')

def is_interesting(filename):
    name_lower = filename.lower()
    ext = os.path.splitext(name_lower)[1]

    if ext in INTERESTING_EXTENSIONS:
        return True
    if any(keyword in name_lower for keyword in INTERESTING_KEYWORDS):
        return True
    return False


def format_size(size):
    # Convert raw byte count into a readable string
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def enumerate_share(conn, share, path='', depth=0, flagged=None, download=False, download_dir='loot', out=None):
    if flagged is None:
        flagged = []

    indent = '  ' * depth

    try:
        entries = conn.listPath(share, path + '\\*')
    except Exception as e:
        log(Fore.RED + f"{indent}  [!] Could not list {path}: {e}", out)
        return

    for entry in entries:
        name = entry.get_longname()

        if name in ('.', '..'):
            continue

        full_path = f"{path}\\{name}"

        if entry.is_directory():
            log(Fore.BLUE + f"{indent}{name}/", out)
            enumerate_share(conn, share, full_path, depth + 1, flagged, download, download_dir, out)

        else:
            size = format_size(entry.get_filesize())

            if is_interesting(name):
                log(Fore.YELLOW + f"{indent}[!] {name} ({size})", out)
                flagged.append(full_path)

                if download:
                    local_dir = os.path.join(download_dir, os.path.dirname(full_path).lstrip('\\'))
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, name)
                    try:
                        with open(local_path, 'wb') as f:
                            conn.getFile(share, full_path, f.write)
                    except Exception as e:
                        log(Fore.RED + f"{indent}       -> Download failed: {e}", out)
            else:
                log(Fore.WHITE + f"{indent}{name} ({size})", out)


def main():
    
    parser = argparse.ArgumentParser(
        description='Recursively enumerate an SMB share and flag files of interest.'
    )
    parser.add_argument('-H', metavar='HOST', dest='host', required=True, help='Target IP or hostname (required)')
    parser.add_argument('-u', metavar='USERNAME', dest='username', default='', help='Username (default: blank)')
    parser.add_argument('-p', metavar='PASSWORD', dest='password', default='', help='Password (default: blank)')
    parser.add_argument('-d', metavar='DOMAIN', dest='domain', default='', help='Target domain')
    parser.add_argument('-s', metavar='SHARE', dest='share', required=True, help='Share name to enumerate (required)')
    parser.add_argument('--ext-file', default=None, help='Path to a file containing additional interesting extensions (one per line)')
    parser.add_argument('--kw-file', default=None, help='Path to a file containing additional interesting keywords (one per line)')
    parser.add_argument('--download', action='store_true', help='Automatically download flagged files')
    parser.add_argument('--loot-dir', default='loot', help='Directory to save downloaded files (default: ./loot)')
    parser.add_argument('--output', default=None, help='Save the output to a text file')
    args = parser.parse_args()

    if args.ext_file:
        with open(args.ext_file, 'r') as f:
            extras = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            INTERESTING_EXTENSIONS.extend(extras)

    if args.kw_file:
        with open(args.kw_file, 'r') as f:
            extras = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            INTERESTING_KEYWORDS.extend(extras)

    if args.output:
        out = open(args.output, 'w', encoding='utf-8')
    else:
        out = None

    print_banner()

    # Connect to the target
    print(Fore.CYAN + f"[*] Connecting to {args.host}...")
    try:
        conn = SMBConnection(args.host, args.host)
    except Exception as e:
        print(Fore.RED + f"[!] Connection failed: {e}")
        sys.exit(1)

    try:
        conn.login(args.username, args.password, args.domain)
        auth_type = "anonymous" if not args.username else f"'{args.username}'"
        print(Fore.GREEN + f"[+] Authenticated as {auth_type}")
    except Exception as e:
        print(Fore.RED + f"[!] Authentication failed: {e}")
        sys.exit(1)

    # Start recursive enumeration
    print(Fore.CYAN + f"[*] Enumerating share: {args.share}\n")
    print(Fore.WHITE + "-" * 60)

    flagged = []
    enumerate_share(conn, args.share, flagged=flagged, download=args.download, download_dir=args.loot_dir, out=out)

    # Print summary of flagged files
    print(Fore.WHITE + "\n" + "-" * 60)
    if flagged:
        print(Fore.YELLOW + f"\n[!] {len(flagged)} file(s) of interest identified:\n")
        for f in flagged:
            print(Fore.YELLOW + f"    {f}")
    else:
        print(Fore.WHITE + "\n[*] No files of interest identified.")

    if args.download and flagged:
        print(Fore.GREEN + f"\n[+] Flagged files downloaded to ./{args.loot_dir}/")

    if out:
        out.close()
        print(Fore.GREEN + f"[+] File tree saved to {args.output}")

    conn.logoff()
    print(Fore.CYAN + "\n[*] Done\n")


if __name__ == '__main__':
    main()
