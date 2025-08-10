#!/usr/bin/env python3
"""
Touch Log Viewer for Raspberry Pi
A touchscreen-controlled log monitoring tool optimized for Raspberry Pi systems.
"""
import subprocess
import time
import signal
import sys
import os
import re
import tempfile
from pathlib import Path

# Try to import evdev, provide fallback if not available
try:
    import evdev
    from evdev import ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    print("Warning: evdev not available. Touch functionality will be limited.")
    print("Install with: sudo apt install python3-evdev")

# ANSI Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Status code colors
    SUCCESS = '\033[92m'    # Green for 2xx
    REDIRECT = '\033[93m'   # Yellow for 3xx  
    CLIENT_ERR = '\033[91m' # Red for 4xx
    SERVER_ERR = '\033[95m' # Magenta for 5xx
    
    # Component colors
    IP = '\033[96m'         # Cyan for IP addresses
    TIME = '\033[94m'       # Blue for timestamps
    METHOD = '\033[97m'     # White for HTTP methods
    PATH = '\033[90m'       # Gray for paths
    UA = '\033[33m'         # Dark yellow for user agents
    SIZE = '\033[35m'       # Purple for response sizes

def format_compact_apache_log(line):
    """
    Convert Apache access log to compact, color-coded format for small screens
    Original: 167.94.145.97 - - [10/Aug/2025:22:16:22 +0100] "GET /sitemap.xml HTTP/1.1" 301 429 "-" "Mozilla/5.0..."
    Compact:  22:16 167.94.145.97 GET /sitemap.xml 301 429b Mozilla/5.0...
    """
    # Apache Combined Log Format regex
    log_pattern = r'(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) ([^"]*) ([^"]*)" (\d+) (\S+) "[^"]*" "([^"]*)"'
    
    match = re.match(log_pattern, line.strip())
    if not match:
        return line  # Return original if parsing fails
    
    ip, timestamp, method, path, protocol, status, size, user_agent = match.groups()
    
    # Extract time (HH:MM) from timestamp
    time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', timestamp)
    if time_match:
        time_str = f"{time_match.group(1)}:{time_match.group(2)}"
    else:
        time_str = "??:??"
    
    # Truncate long paths for readability
    if len(path) > 25:
        path = path[:22] + "..."
    
    # Truncate user agent but keep useful info
    ua_short = user_agent[:30] + "..." if len(user_agent) > 30 else user_agent
    
    # Remove common prefixes
    ua_short = ua_short.replace("Mozilla/5.0 ", "")
    ua_short = ua_short.replace("(compatible; ", "")
    
    # Color coding based on status code
    status_int = int(status)
    if 200 <= status_int < 300:
        status_color = Colors.SUCCESS
    elif 300 <= status_int < 400:
        status_color = Colors.REDIRECT
    elif 400 <= status_int < 500:
        status_color = Colors.CLIENT_ERR
    elif 500 <= status_int < 600:
        status_color = Colors.SERVER_ERR
    else:
        status_color = Colors.RESET
    
    # Format size with appropriate unit
    try:
        size_int = int(size) if size != '-' else 0
        if size_int < 1024:
            size_str = f"{size_int}b"
        elif size_int < 1024*1024:
            size_str = f"{size_int//1024}k"
        else:
            size_str = f"{size_int//(1024*1024)}M"
    except:
        size_str = size
    
    # Build compact format with colors
    compact = (f"{Colors.TIME}{time_str}{Colors.RESET} "
              f"{Colors.IP}{ip:<15}{Colors.RESET} "
              f"{Colors.METHOD}{method:<4}{Colors.RESET} "
              f"{Colors.PATH}{path:<25}{Colors.RESET} "
              f"{status_color}{status}{Colors.RESET} "
              f"{Colors.SIZE}{size_str:<5}{Colors.RESET} "
              f"{Colors.UA}{ua_short}{Colors.RESET}")
    
    return compact

class TouchLogViewer:
    def __init__(self):
        self.current_view = 0
        self.current_process = None
        self.temp_scripts = []  # Track temporary formatter scripts
        
        # Detect available logs automatically
        self.log_paths = self.detect_available_logs()
        
        # Build views based on available logs
        self.views = self.build_available_views()
        
        if not self.views:
            print("No suitable log files found! Please check your system logs.")
            print("Available log directories to check:")
            for log_dir in ['/var/log', '/var/log/apache2', '/var/log/nginx']:
                if os.path.exists(log_dir):
                    print(f"  {log_dir}")
            sys.exit(1)
        
        # Find touchscreen device if evdev is available
        if EVDEV_AVAILABLE:
            self.touchscreen = self.find_touchscreen()
            if not self.touchscreen:
                print("No touchscreen found! Available devices:")
                for device in evdev.list_devices():
                    dev = evdev.InputDevice(device)
                    print(f"  {dev.path}: {dev.name}")
                print("\nContinuing without touch support. Use Ctrl+C to switch views manually.")
                self.touchscreen = None
            else:
                print(f"Using touchscreen: {self.touchscreen.name}")
        else:
            self.touchscreen = None
            print("Touch support disabled (evdev not available)")
    
    def detect_available_logs(self):
        """Detect available log files on the system"""
        possible_logs = {
            # System logs
            'syslog': '/var/log/syslog',
            'auth': '/var/log/auth.log',
            'kern': '/var/log/kern.log',
            'daemon': '/var/log/daemon.log',
            'messages': '/var/log/messages',
            
            # Web server logs - Main site (zemia.uk)
            'zemia_access': '/var/log/apache2/zemia-access.log',
            'zemia_error': '/var/log/apache2/zemia-error.log',
            
            # Web server logs - Dev site (dev.zemia.uk)  
            'dev_zemia_access': '/var/log/apache2/dev-zemia-access.log',
            'dev_zemia_error': '/var/log/apache2/dev-zemia-error.log',
            
            # Generic Apache/Nginx logs (fallback)
            'apache_access': '/var/log/apache2/access.log',
            'apache_error': '/var/log/apache2/error.log',
            'apache_other_vhosts': '/var/log/apache2/other_vhosts_access.log',
            'nginx_access': '/var/log/nginx/access.log',
            'nginx_error': '/var/log/nginx/error.log',
            
            # Alternative common paths
            'apache_access_alt': '/var/log/httpd/access_log',
            'apache_error_alt': '/var/log/httpd/error_log',
            
            # Application logs (customize these for your setup)
            'custom_app': '/home/pi/logs/app.log',
        }
        
        available_logs = {}
        for name, path in possible_logs.items():
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    # Test if we can read the file
                    with open(path, 'r') as f:
                        f.read(1)
                    available_logs[name] = path
                except (PermissionError, IOError):
                    # Skip files we can't read
                    continue
                    
        return available_logs
    
    def create_formatter_script(self):
        """Create a Python script that formats Apache logs in compact format"""
        formatter_script = '''#!/usr/bin/env python3
import sys
import re

# Color constants
class Colors:
    RESET = '\\033[0m'
    SUCCESS = '\\033[92m'    # Green for 2xx
    REDIRECT = '\\033[93m'   # Yellow for 3xx  
    CLIENT_ERR = '\\033[91m' # Red for 4xx
    SERVER_ERR = '\\033[95m' # Magenta for 5xx
    IP = '\\033[96m'         # Cyan for IP addresses
    TIME = '\\033[94m'       # Blue for timestamps
    METHOD = '\\033[97m'     # White for HTTP methods
    PATH = '\\033[90m'       # Gray for paths
    UA = '\\033[33m'         # Dark yellow for user agents
    SIZE = '\\033[35m'       # Purple for response sizes

def format_compact_log(line):
    log_pattern = r'(\\S+) \\S+ \\S+ \\[([^\\]]+)\\] "(\\S+) ([^"]*) ([^"]*)" (\\d+) (\\S+) "[^"]*" "([^"]*)"'
    
    match = re.match(log_pattern, line.strip())
    if not match:
        return line
    
    ip, timestamp, method, path, protocol, status, size, user_agent = match.groups()
    
    # Extract time (HH:MM)
    time_match = re.search(r'(\\d{2}):(\\d{2}):(\\d{2})', timestamp)
    time_str = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else "??:??"
    
    # Truncate long paths
    if len(path) > 50:
        path = path[:47] + "..."
    
    # Truncate user agent
    ua_short = user_agent[:30] + "..." if len(user_agent) > 30 else user_agent
    ua_short = ua_short.replace("Mozilla/5.0 ", "").replace("(compatible; ", "")
    
    # Color coding
    status_int = int(status)
    if 200 <= status_int < 300:
        status_color = Colors.SUCCESS
    elif 300 <= status_int < 400:
        status_color = Colors.REDIRECT  
    elif 400 <= status_int < 500:
        status_color = Colors.CLIENT_ERR
    elif 500 <= status_int < 600:
        status_color = Colors.SERVER_ERR
    else:
        status_color = Colors.RESET
    
    # Format size
    try:
        size_int = int(size) if size != '-' else 0
        if size_int < 1024:
            size_str = f"{size_int}b"
        elif size_int < 1024*1024:
            size_str = f"{size_int//1024}k"
        else:
            size_str = f"{size_int//(1024*1024)}M"
    except:
        size_str = size
    
    # Build compact format
    compact = (f"{Colors.TIME}{time_str}{Colors.RESET} "
              f"{Colors.IP}{ip:<15}{Colors.RESET} "
              f"{Colors.METHOD}{method:<4}{Colors.RESET} "
              f"{Colors.PATH}{path:<25}{Colors.RESET} "
              f"{status_color}{status}{Colors.RESET} "
              f"{Colors.SIZE}{size_str:<5}{Colors.RESET} "
              f"{Colors.UA}{ua_short}{Colors.RESET}")
    
    return compact

# Process stdin line by line
for line in sys.stdin:
    print(format_compact_log(line))
'''
        
        # Create temporary formatter script
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(formatter_script)
        temp_file.close()
        
        # Make executable and track for cleanup
        os.chmod(temp_file.name, 0o755)
        self.temp_scripts.append(temp_file.name)
        
        return temp_file.name
    
    def build_available_views(self):
        """Build view list based on available logs and tools"""
        views = []
        
        # Check which tools are available
        tools_available = {
            'tmux': self.check_command('tmux'),
            'multitail': self.check_command('multitail'),
            'htop': self.check_command('htop'),
            'top': self.check_command('top'),
        }
        
        # System stats view (always available)
        if tools_available['htop']:
            views.append({
                'name': 'System Stats (htop)',
                'command': self.start_htop
            })
        elif tools_available['top']:
            views.append({
                'name': 'System Stats (top)',
                'command': self.start_top
            })
        
        # Single log views for major logs (prioritize your custom logs)
        priority_logs = [
            'zemia_access', 'zemia_error',           # Main site logs first
            'dev_zemia_access', 'dev_zemia_error',   # Dev site logs second
            'syslog', 'auth',                        # System logs
            'apache_access', 'apache_error',         # Generic Apache logs (fallback)
            'nginx_access', 'nginx_error'            # Nginx logs
        ]
        for log_name in priority_logs:
            if log_name in self.log_paths:
                views.append({
                    'name': f'{log_name.replace("_", " ").title()} Log',
                    'command': lambda path=self.log_paths[log_name]: self.start_single_log(path)
                })
        
        # Add combined views for your sites
        if 'zemia_access' in self.log_paths and 'zemia_error' in self.log_paths:
            views.append({
                'name': 'Main Site (zemia.uk) - All Logs',
                'command': lambda: self.start_site_logs('zemia')
            })
            
        if 'dev_zemia_access' in self.log_paths and 'dev_zemia_error' in self.log_paths:
            views.append({
                'name': 'Dev Site (dev.zemia.uk) - All Logs', 
                'command': lambda: self.start_site_logs('dev_zemia')
            })
        
        # Multi-log views if tmux or multitail available
        if tools_available['tmux'] and len(self.log_paths) >= 2:
            # Add special 4-panel view for your sites if available
            if ('zemia_access' in self.log_paths and 'zemia_error' in self.log_paths and
                'dev_zemia_access' in self.log_paths and 'dev_zemia_error' in self.log_paths):
                views.append({
                    'name': 'TMUX 4-Panel: Main + Dev Sites',
                    'command': self.start_tmux_apache_view
                })
            
            views.append({
                'name': 'TMUX Multi-Panel View (All Logs)',
                'command': self.start_tmux_multiview
            })
        
        if tools_available['multitail'] and len(self.log_paths) >= 2:
            views.append({
                'name': 'Multitail Combined View',
                'command': self.start_multitail_combined
            })
        
        # Pi-specific system monitoring
        views.append({
            'name': 'Pi System Monitor',
            'command': self.start_pi_monitor
        })
        
        return views
    
    def check_command(self, command):
        """Check if a command is available on the system"""
        try:
            result = subprocess.run(['which', command], capture_output=True, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except:
            return False
        
    def find_touchscreen(self):
        """Find the touchscreen device"""
        if not EVDEV_AVAILABLE:
            return None
            
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        # Look for touchscreen-like devices (prioritize ft5406 for Pi touchscreen)
        touchscreen_keywords = ['ft5406', 'touch', 'screen', 'finger']
        
        for device in devices:
            device_name = device.name.lower()
            if any(keyword in device_name for keyword in touchscreen_keywords):
                # Check if it has touch capabilities (absolute positioning)
                caps = device.capabilities()
                if 3 in caps:  # EV_ABS = 3
                    return device
                    
        # Fallback: return any device with absolute positioning
        for device in devices:
            caps = device.capabilities()
            if 3 in caps:  # EV_ABS = 3
                return device
                
        return None
    
    def kill_current_process(self):
        """Kill current viewing process"""
        if self.current_process:
            try:
                # Kill both possible tmux sessions
                subprocess.run(['tmux', 'kill-session', '-t', 'logmonitoring'], 
                             capture_output=True)
                subprocess.run(['tmux', 'kill-session', '-t', 'apachelogs'], 
                             capture_output=True)
                
                # Kill the process
                self.current_process.terminate()
                time.sleep(0.5)
                if self.current_process.poll() is None:
                    self.current_process.kill()
                    
            except Exception as e:
                print(f"Error killing process: {e}")
            finally:
                self.current_process = None
    
    def start_single_log(self, log_path):
        """Start viewing a single log file with compact formatting for Apache logs"""
        print(f"Starting single log view: {log_path}")
        
        # Check if this is an Apache access log and apply compact formatting
        if ('access' in log_path.lower() and 
            ('apache' in log_path.lower() or 'zemia' in log_path.lower())):
            print("🎨 Using compact format for Apache access log...")
            
            # Create the formatter script
            formatter_script = self.create_formatter_script()
            
            # Use tail with the formatter
            if os.access(log_path, os.R_OK):
                cmd = f'sudo tail -f {log_path} | python3 {formatter_script}'
            else:
                cmd = f'tail -f {log_path} | python3 {formatter_script}'
            
            self.current_process = subprocess.Popen(cmd, shell=True)
        else:
            # Standard tail for non-Apache logs
            cmd = ['sudo', 'tail', '-f', log_path] if os.access(log_path, os.R_OK) else ['tail', '-f', log_path]
            self.current_process = subprocess.Popen(cmd)
    
    def start_htop(self):
        """Start htop system monitor"""
        print("Starting htop system monitor...")
        cmd = ['htop']
        self.current_process = subprocess.Popen(cmd)
    
    def start_top(self):
        """Start top system monitor"""
        print("Starting top system monitor...")
        cmd = ['top']
        self.current_process = subprocess.Popen(cmd)
    
    def start_tmux_multiview(self):
        """Start tmux multi-panel view with available logs"""
        print("Starting TMUX Multi-Panel View...")
        
        # Kill any existing tmux session
        subprocess.run(['tmux', 'kill-session', '-t', 'logmonitoring'], 
                      capture_output=True, stderr=subprocess.DEVNULL)
        
        # Create tmux session
        subprocess.run(['tmux', 'new-session', '-d', '-s', 'logmonitoring'])
        
        # Get up to 4 most important logs
        available_logs = list(self.log_paths.items())[:4]
        
        # Create panes based on number of logs
        if len(available_logs) > 1:
            subprocess.run(['tmux', 'split-window', '-h'])
        if len(available_logs) > 2:
            subprocess.run(['tmux', 'select-pane', '-t', '0'])
            subprocess.run(['tmux', 'split-window', '-v'])
        if len(available_logs) > 3:
            subprocess.run(['tmux', 'select-pane', '-t', '2'])
            subprocess.run(['tmux', 'split-window', '-v'])
        
        # Start logs in each pane
        for i, (name, path) in enumerate(available_logs):
            # Check if this is an Apache access log
            if 'access' in name.lower() and ('apache' in path.lower() or 'zemia' in path.lower()):
                formatter_script = self.create_formatter_script()
                cmd = f'echo "=== {name.upper().replace("_", " ")} (COMPACT) ===" && sudo tail -f {path} | python3 {formatter_script}'
            else:
                cmd = f'echo "=== {name.upper().replace("_", " ")} ===" && sudo tail -f {path}'
            
            subprocess.run(['tmux', 'send-keys', '-t', str(i), cmd, 'Enter'])
        
        # Attach to session
        self.current_process = subprocess.Popen(['tmux', 'attach', '-t', 'logmonitoring'])
    
    def start_multitail_combined(self):
        """Start multitail with available logs"""
        print("Starting Multitail Combined View...")
        cmd = ['sudo', 'multitail']
        
        # Add each available log with a label
        for name, path in list(self.log_paths.items())[:6]:  # Limit to 6 logs for readability
            cmd.extend(['-l', name.replace('_', ' ').title(), '-l', f'tail -f {path}'])
        
        self.current_process = subprocess.Popen(cmd)
    
    def start_pi_monitor(self):
        """Start Raspberry Pi specific monitoring"""
        print("Starting Pi System Monitor...")
        
        # Create a simple monitoring script
        monitor_script = '''
clear
echo "=== Raspberry Pi System Monitor ==="
echo "Press Ctrl+C to exit"
echo ""

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo "----------------------------------------"
    
    # CPU Temperature
    if command -v vcgencmd &> /dev/null; then
        echo "CPU Temperature: $(vcgencmd measure_temp)"
    fi
    
    # CPU Usage
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')"
    
    # Memory
    echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3"/"$2" ("$3/$2*100"%)"}')"
    
    # Disk
    echo "Disk /: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
    
    # Network (if wlan0 exists)
    if ip addr show wlan0 &>/dev/null; then
        echo "WiFi IP: $(ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)"
    fi
    
    # GPU Memory split (Pi specific)
    if command -v vcgencmd &> /dev/null; then
        echo "GPU Memory: $(vcgencmd get_mem gpu)"
    fi
    
    echo "----------------------------------------"
    echo ""
    sleep 5
    clear
done
'''
        
        # Write the monitor script to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(monitor_script)
            script_path = f.name
        
        # Make it executable and run it
        os.chmod(script_path, 0o755)
        self.current_process = subprocess.Popen(['bash', script_path])
    
    def start_site_logs(self, site_prefix):
        """Start viewing logs for a specific site (zemia or dev_zemia)"""
        access_key = f'{site_prefix}_access'
        error_key = f'{site_prefix}_error'
        
        access_log = self.log_paths.get(access_key)
        error_log = self.log_paths.get(error_key)
        
        if not access_log or not error_log:
            print(f"Logs for {site_prefix} not found!")
            return
            
        if self.check_command('multitail'):
            print(f"Starting {site_prefix} site logs with multitail...")
            site_name = "Main Site" if site_prefix == "zemia" else "Dev Site"
            cmd = ['sudo', 'multitail', 
                   '-l', f'{site_name} Access Log', access_log,
                   '-l', f'{site_name} Error Log', error_log]
            self.current_process = subprocess.Popen(cmd)
        else:
            # Fallback to just access log
            print(f"Starting {site_prefix} access log (multitail not available)...")
            self.start_single_log(access_log)
    
    def start_tmux_apache_view(self):
        """Start a 4-panel tmux view specifically for Apache logs"""
        print("Starting TMUX 4-Panel Apache View...")
        
        # Kill any existing tmux session
        subprocess.run(['tmux', 'kill-session', '-t', 'apachelogs'], 
                      capture_output=True, stderr=subprocess.DEVNULL)
        
        # Create tmux session
        subprocess.run(['tmux', 'new-session', '-d', '-s', 'apachelogs'])
        
        # Create 4 panes (2x2 grid)
        subprocess.run(['tmux', 'split-window', '-h'])     # Split horizontally
        subprocess.run(['tmux', 'select-pane', '-t', '0']) # Select left pane
        subprocess.run(['tmux', 'split-window', '-v'])     # Split vertically
        subprocess.run(['tmux', 'select-pane', '-t', '2']) # Select right pane  
        subprocess.run(['tmux', 'split-window', '-v'])     # Split vertically
        
        # Start logs in each pane
        logs_config = [
            (0, "MAIN SITE ACCESS (zemia.uk)", self.log_paths.get('zemia_access')),
            (1, "MAIN SITE ERRORS (zemia.uk)", self.log_paths.get('zemia_error')),
            (2, "DEV SITE ACCESS (dev.zemia.uk)", self.log_paths.get('dev_zemia_access')),
            (3, "DEV SITE ERRORS (dev.zemia.uk)", self.log_paths.get('dev_zemia_error'))
        ]
        
        for pane, title, log_path in logs_config:
            if log_path:
                # Use compact format for access logs
                if 'ACCESS' in title:
                    formatter_script = self.create_formatter_script()
                    cmd = f'echo "=== {title} (COMPACT) ===" && echo "" && sudo tail -f {log_path} | python3 {formatter_script}'
                else:
                    cmd = f'echo "=== {title} ===" && echo "" && sudo tail -f {log_path}'
                subprocess.run(['tmux', 'send-keys', '-t', str(pane), cmd, 'Enter'])
            else:
                cmd = f'echo "=== {title} ===" && echo "Log file not found: {log_path}"'
                subprocess.run(['tmux', 'send-keys', '-t', str(pane), cmd, 'Enter'])
        
        # Attach to session
        self.current_process = subprocess.Popen(['tmux', 'attach', '-t', 'apachelogs'])
    
    # Keep the original methods for backwards compatibility
    def start_tmux_view(self):
        """Legacy method - redirect to new multiview"""
        self.start_tmux_multiview()
    
    def start_multitail_all(self):
        """Legacy method - redirect to new combined view"""
        self.start_multitail_combined()
    
    def start_main_access_only(self):
        """Start main site access log if available"""
        if 'apache_access' in self.log_paths:
            self.start_single_log(self.log_paths['apache_access'])
        elif 'nginx_access' in self.log_paths:
            self.start_single_log(self.log_paths['nginx_access'])
        else:
            print("No web server access log found")
    
    def start_dev_access_only(self):
        """Start dev site access log if available"""
        # Try to find a dev-specific log
        for name, path in self.log_paths.items():
            if 'dev' in name or 'development' in name:
                self.start_single_log(path)
                return
        print("No development log found")
    
    def start_errors_only(self):
        """Start error logs only"""
        error_logs = [(name, path) for name, path in self.log_paths.items() if 'error' in name]
        
        if not error_logs:
            print("No error logs found")
            return
            
        if len(error_logs) == 1:
            self.start_single_log(error_logs[0][1])
        else:
            # Use multitail for multiple error logs
            cmd = ['sudo', 'multitail']
            for name, path in error_logs:
                cmd.extend(['-l', name.replace('_', ' ').title(), '-l', f'tail -f {path}'])
            self.current_process = subprocess.Popen(cmd)
    
    def start_system_stats(self):
        """Legacy method - redirect to htop or top"""
        if self.check_command('htop'):
            self.start_htop()
        else:
            self.start_top()
    
    def switch_view(self):
        """Switch to next view"""
        self.kill_current_process()
        time.sleep(0.5)  # Give time for cleanup
        
        view = self.views[self.current_view]
        print(f"\n🔄 Switching to view {self.current_view + 1}/{len(self.views)}: {view['name']}")
        print("=" * 60)
        
        try:
            view['command']()
            self.current_view = (self.current_view + 1) % len(self.views)
            print(f"Next touch will show: {self.views[self.current_view]['name']}")
        except Exception as e:
            print(f"❌ Error starting view: {e}")
            # Try to move to next view anyway
            self.current_view = (self.current_view + 1) % len(self.views)
    
    def listen_for_touches(self):
        """Listen for touch events or provide manual control"""
        print(f"Available views: {len(self.views)}")
        for i, view in enumerate(self.views):
            print(f"  {i+1}. {view['name']}")
        print()
        
        if self.touchscreen:
            print("Touch screen to cycle through log views...")
            print("Press Ctrl+C to exit")
            
            # Start with first view
            self.switch_view()
            
            last_touch_time = 0
            debounce_time = 1.0  # 1 second debounce
            
            try:
                for event in self.touchscreen.read_loop():
                    # Check for touch events (BTN_TOUCH = 330, EV_KEY = 1)
                    if event.type == 1 and event.code == 330:
                        if event.value == 1:  # Touch down
                            current_time = time.time()
                            if current_time - last_touch_time > debounce_time:
                                print("\n🖱️  Touch detected! Switching view...")
                                self.switch_view()
                                last_touch_time = current_time
                                
            except KeyboardInterrupt:
                print("\nExiting...")
            finally:
                self.cleanup()
        else:
            # Fallback mode without touch
            print("Touch screen not available. Using keyboard control mode.")
            print("Press SPACE to switch views, 'q' to quit, or Ctrl+C to exit")
            
            # Start with first view
            self.switch_view()
            
            try:
                while True:
                    try:
                        # Simple input polling
                        import select
                        import sys
                        import tty
                        import termios
                        
                        old_settings = termios.tcgetattr(sys.stdin)
                        tty.setraw(sys.stdin.fileno())
                        
                        if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
                            key = sys.stdin.read(1)
                            if key == ' ':  # Space to switch
                                print("\n⌨️  Switching view...")
                                self.switch_view()
                            elif key.lower() == 'q':  # Q to quit
                                break
                                
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        time.sleep(0.1)
                        
                    except:
                        # Fallback: just run first view and wait for Ctrl+C
                        print("Keyboard control not available. Press Ctrl+C to exit.")
                        while True:
                            time.sleep(1)
                        
            except KeyboardInterrupt:
                print("\nExiting...")
            finally:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except:
                    pass
                self.cleanup()
    
    def cleanup(self):
        """Clean up processes and tmux sessions"""
        print("Cleaning up...")
        self.kill_current_process()
        
        # Clean up temporary formatter scripts
        for script_path in self.temp_scripts:
            try:
                os.unlink(script_path)
            except:
                pass
        self.temp_scripts.clear()
        
        # Final cleanup of tmux sessions
        subprocess.run(['tmux', 'kill-session', '-t', 'logmonitoring'], 
                      capture_output=True, stderr=subprocess.DEVNULL)
        subprocess.run(['tmux', 'kill-session', '-t', 'apachelogs'], 
                      capture_output=True, stderr=subprocess.DEVNULL)
        print("Goodbye!")

def main():
    viewer = TouchLogViewer()
    viewer.listen_for_touches()

if __name__ == "__main__":
    main()