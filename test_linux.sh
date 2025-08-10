#!/bin/bash
# Test script for PS-Utils on Linux/Raspberry Pi OS

echo "=== PS-Utils Linux Test Script ==="
echo "=================================="

# Test 1: Check if Python scripts exist
echo "1. Checking Python scripts..."
SCRIPTS_DIR="$(dirname "$0")/scripts"
for script in "$SCRIPTS_DIR"/*.py; do
    if [ -f "$script" ]; then
        echo "  ✓ Found: $(basename "$script")"
    fi
done

echo ""

# Test 2: Check Python dependencies
echo "2. Checking Python dependencies..."

# Check basic Python
if command -v python3 &> /dev/null; then
    echo "  ✓ Python 3: $(python3 --version)"
else
    echo "  ✗ Python 3: Not found"
fi

# Check specific modules
modules=("argparse" "fnmatch" "os" "subprocess")
for module in "${modules[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        echo "  ✓ Python module: $module"
    else
        echo "  ✗ Python module: $module"
    fi
done

# Check optional modules
echo "  Optional modules:"
if python3 -c "import PIL" 2>/dev/null; then
    echo "    ✓ PIL (Pillow) - for heightmap-to-watermap"
else
    echo "    ✗ PIL (Pillow) - install with: pip3 install Pillow"
fi

if python3 -c "import evdev" 2>/dev/null; then
    echo "    ✓ evdev - for touch-log-viewer"
else
    echo "    ✗ evdev - install with: sudo apt install python3-evdev"
fi

echo ""

# Test 3: Check system tools
echo "3. Checking system tools..."
tools=("tmux" "multitail" "htop" "git")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "  ✓ $tool"
    else
        echo "  ✗ $tool - install with: sudo apt install $tool"
    fi
done

echo ""

# Test 4: Check Raspberry Pi specific features
echo "4. Checking Raspberry Pi features..."
if [ -f "/proc/device-tree/model" ]; then
    model=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')
    echo "  ✓ Pi Model: $model"
else
    echo "  ℹ Not running on Raspberry Pi (or model info unavailable)"
fi

if command -v vcgencmd &> /dev/null; then
    temp=$(vcgencmd measure_temp 2>/dev/null)
    echo "  ✓ vcgencmd available: $temp"
else
    echo "  ✗ vcgencmd not available (Pi-specific tool)"
fi

# Check for input devices (touchscreen)
if [ -d "/dev/input" ]; then
    touch_devices=$(ls /dev/input/event* 2>/dev/null | wc -l)
    echo "  ✓ Input devices: $touch_devices event devices found"
else
    echo "  ✗ Input devices: /dev/input not found"
fi

echo ""

# Test 5: Test individual scripts
echo "5. Testing individual scripts..."

# Test combine_files
echo "  Testing combine-files..."
if python3 "$SCRIPTS_DIR/combine_files.py" --help &>/dev/null; then
    echo "    ✓ combine-files help works"
else
    echo "    ✗ combine-files help failed"
fi

# Test heightmap_to_watermap
echo "  Testing heightmap-to-watermap..."
if python3 "$SCRIPTS_DIR/heightmap_to_watermap.py" --help &>/dev/null; then
    echo "    ✓ heightmap-to-watermap help works"
else
    echo "    ✗ heightmap-to-watermap help failed (may need PIL)"
fi

# Test touch_log_viewer
echo "  Testing touch-log-viewer..."
if python3 -c "
import sys
sys.path.insert(0, '$SCRIPTS_DIR')
try:
    from touch_log_viewer import TouchLogViewer
    viewer = TouchLogViewer()
    print('    ✓ touch-log-viewer imports successfully')
except Exception as e:
    print(f'    ✗ touch-log-viewer import failed: {e}')
"; then
    :  # Success message already printed
fi

echo ""

# Summary
echo "=== Test Summary ==="
echo "If you see any ✗ marks above, those dependencies need to be installed."
echo "Run the setup script to install missing dependencies:"
echo "  ./setup_linux.sh"
echo ""
echo "For a complete installation test, run:"
echo "  ./setup_linux.sh && source ~/.bashrc"
echo "Then test the commands:"
echo "  combine-files --help"
echo "  heightmap-to-watermap --help"
echo "  touch-log-viewer  # (requires sudo for some log files)"
