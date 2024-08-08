#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    
    if "dovecot: " in line:
        if "Jun " in line:
            if "imap-login" in line:
                user_str = line.split(" ")[7]
                username = user_str.split("=<")[-1].replace(">,", "")
                print(f"1\t{username}")
