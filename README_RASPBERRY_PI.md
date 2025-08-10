# PS-Utils for Raspberry Pi

This document provides specific information for using PS-Utils on Raspberry Pi OS (formerly Raspbian).

## Quick Start for Pi Users

```bash
# 1. Clone the repository
git clone https://github.com/OK-Diamond/PS-Utils.git
cd PS-Utils

# 2. Run the setup (will install dependencies automatically)
./setup_linux.sh

# 3. Restart your terminal or source your profile
source ~/.bashrc

# 4. Test the installation
./test_linux.sh
```

## Raspberry Pi Specific Features

### Touch Log Viewer

The `touch-log-viewer` command is specially optimized for Raspberry Pi touchscreens:

- **Official Pi Touchscreen Support**: Automatically detects the ft5406 touchscreen driver
- **System Monitoring**: Shows Pi-specific metrics like CPU temperature and GPU memory
- **Log Detection**: Automatically finds common log files on Pi OS
- **Fallback Modes**: Works without touchscreen using keyboard controls

#### Supported Log Files

The tool automatically detects and monitors:

- System logs: `/var/log/syslog`, `/var/log/auth.log`, `/var/log/kern.log`
- Web server logs: Apache2 and Nginx (if installed)
- Custom application logs (configurable)

#### Pi System Monitor View

Displays real-time information:
- CPU temperature (using `vcgencmd`)
- Memory usage
- Disk space
- Network status (WiFi IP)
- GPU memory allocation
- System load

### Hardware Requirements

- **Minimum**: Raspberry Pi 3B+ or newer
- **Recommended**: Raspberry Pi 4B or Pi 5 for best performance
- **Touchscreen**: Official Pi touchscreen or compatible capacitive touchscreen
- **Storage**: At least 1GB free space for logs and dependencies

### Permissions Setup

The setup script automatically:
1. Adds your user to the `input` group for touchscreen access
2. Sets up sudo permissions for log file access
3. Installs system dependencies via apt

**Note**: You may need to log out and back in after setup for group changes to take effect.

## Dependencies Installed

The Linux setup script automatically installs:

- `python3-evdev`: Touchscreen input handling
- `tmux`: Terminal multiplexer for multi-panel views
- `multitail`: Multiple log file viewer
- `htop`: System process monitor
- `python3-pip`: Python package manager (if needed)

Python packages installed:
- `Pillow`: Image processing for heightmap tools

## Customization

### Log Paths

Edit the log paths in `touch_log_viewer.py` or create a config file:

```python
# Custom log paths example
custom_logs = {
    'my_app': '/home/pi/logs/myapp.log',
    'home_automation': '/var/log/homeassistant/homeassistant.log',
    'pihole': '/var/log/pihole.log',
}
```

### Touchscreen Sensitivity

Adjust the debounce time for touch sensitivity:

```python
# In touch_log_viewer.py
debounce_time = 1.0  # Seconds between touch events
```

## Troubleshooting

### Touchscreen Not Detected

1. Check if touchscreen is connected:
   ```bash
   ls /dev/input/event*
   ```

2. Check evdev installation:
   ```bash
   python3 -c "import evdev; print('evdev OK')"
   ```

3. Check user permissions:
   ```bash
   groups $USER | grep input
   ```

### Log Files Not Accessible

1. Check file permissions:
   ```bash
   ls -la /var/log/
   ```

2. Test sudo access:
   ```bash
   sudo tail -f /var/log/syslog
   ```

### Performance Issues

For older Pi models (3B and earlier):
- Reduce the number of simultaneous log views
- Use single log view instead of multi-panel tmux
- Increase debounce time for touch events

## Integration with Pi Projects

### Home Automation

Monitor Home Assistant logs:
```bash
# Add to custom_logs in touch_log_viewer.py
'homeassistant': '/home/homeassistant/.homeassistant/home-assistant.log'
```

### Web Server Monitoring

For Apache2 or Nginx setups:
```bash
# Logs are automatically detected at:
# /var/log/apache2/access.log
# /var/log/apache2/error.log
# /var/log/nginx/access.log
# /var/log/nginx/error.log
```

### IoT Projects

Monitor custom application logs by adding them to the log detection in `touch_log_viewer.py`.

## Desktop Integration

The setup script creates a desktop shortcut for GUI users:
- Location: `~/Desktop/touch-log-viewer.desktop`
- Double-click to launch in terminal mode
- Integrates with Pi desktop environment

## Updates

To update PS-Utils:

```bash
cd PS-Utils
git pull origin main
# Re-run setup if new dependencies were added
./setup_linux.sh
```

## Support

For Pi-specific issues:
1. Check the test script output: `./test_linux.sh`
2. Verify Pi model compatibility
3. Ensure all dependencies are installed
4. Check system logs for hardware issues

## Performance Tips

- Use SD card class 10 or better for log file I/O
- Consider using USB storage for heavy logging
- Monitor CPU temperature during intensive log monitoring
- Use single log views on older Pi models for better performance
