#!/usr/bin/env python3
"""
Test script to demonstrate the compact Apache log formatting
"""
import sys
import os

# Add the scripts directory to path so we can import
sys.path.insert(0, '/home/okdiamond/Code/PS-Utils/scripts')
from touch_log_viewer import format_compact_apache_log

# Test log entries from your example
test_logs = [
    '167.94.145.97 - - [10/Aug/2025:22:16:22 +0100] "GET /sitemap.xml HTTP/1.1" 301 429 "-" "Mozilla/5.0 (compatible; CensysInspect/1.1; +https://about.censys.io/)"',
    '66.249.66.165 - - [10/Aug/2025:22:31:35 +0100] "GET /robots.txt HTTP/1.1" 404 3244 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"',
    '43.130.174.37 - - [10/Aug/2025:23:06:21 +0100] "GET / HTTP/1.1" 301 426 "-" "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"',
    '43.130.174.37 - - [10/Aug/2025:23:06:22 +0100] "GET / HTTP/1.1" 200 3869 "http://zemia.uk" "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"',
    '86.131.211.83 - - [10/Aug/2025:23:20:11 +0100] "GET / HTTP/1.1" 200 3921 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0"',
    '86.131.211.83 - - [10/Aug/2025:23:20:11 +0100] "GET /assets/index-C1N0jqG_.css HTTP/1.1" 200 9227 "https://zemia.uk/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0"',
    '86.131.211.83 - - [10/Aug/2025:23:20:11 +0100] "GET /assets/index-B2An_0W6.js HTTP/1.1" 200 88002 "https://zemia.uk/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0"',
    '86.131.211.83 - - [10/Aug/2025:23:20:13 +0100] "GET / HTTP/1.1" 200 1355 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0"'
]

print("🎨 Compact Apache Log Format Demo")
print("=" * 80)
print("Original format:")
print(test_logs[0][:100] + "...")
print()
print("Compact format with color coding:")
print("=" * 80)

for log in test_logs:
    compact = format_compact_apache_log(log)
    print(compact)

print()
print("Key:")
print("Time format: HH:MM (instead of full timestamp)")
print("Size format: b/k/M units (bytes/kilobytes/megabytes)")
print("Path truncated if >25 chars")
print("User agent truncated and cleaned up")
print("Color coding:")
print("  - Green: 2xx (success)")
print("  - Yellow: 3xx (redirect)")
print("  - Red: 4xx (client error)")
print("  - Magenta: 5xx (server error)")
print("  - Cyan: IP addresses")
print("  - Blue: timestamps")
print("  - White: HTTP methods")
