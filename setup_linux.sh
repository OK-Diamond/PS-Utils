#!/bin/bash
# Linux setup script for PS-Utils Command Toolkit
# Optimized for Raspberry Pi OS (Pi500) but works on other Debian/Ubuntu systems

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPTS_DIR="$SCRIPT_DIR/scripts"
USER_BIN_DIR="$HOME/.local/bin"
PROFILE_FILE="$HOME/.bashrc"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}PS-Utils Linux Setup for Raspberry Pi OS${NC}"
echo "============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 first:"
    echo "  sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"

# Create ~/.local/bin if it doesn't exist
if [ ! -d "$USER_BIN_DIR" ]; then
    echo -e "${YELLOW}Creating $USER_BIN_DIR directory...${NC}"
    mkdir -p "$USER_BIN_DIR"
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$USER_BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Adding $USER_BIN_DIR to PATH in $PROFILE_FILE${NC}"
    echo "" >> "$PROFILE_FILE"
    echo "# Added by PS-Utils setup" >> "$PROFILE_FILE"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE_FILE"
fi

# Find all Python scripts
echo -e "${CYAN}Found the following scripts to install:${NC}"
SCRIPTS=()
for script in "$PYTHON_SCRIPTS_DIR"/*.py; do
    if [ -f "$script" ]; then
        basename_script=$(basename "$script" .py)
        command_name=$(echo "$basename_script" | tr '_' '-')
        echo -e "  ${CYAN}- $command_name${NC}"
        SCRIPTS+=("$script:$command_name")
    fi
done

# Check for required dependencies for touch_log_viewer
echo -e "${YELLOW}Checking dependencies for touch-log-viewer...${NC}"
MISSING_DEPS=()

# Check for evdev Python package
if ! python3 -c "import evdev" 2>/dev/null; then
    MISSING_DEPS+=("python3-evdev")
fi

# Check for tmux
if ! command -v tmux &> /dev/null; then
    MISSING_DEPS+=("tmux")
fi

# Check for multitail
if ! command -v multitail &> /dev/null; then
    MISSING_DEPS+=("multitail")
fi

# Check for htop
if ! command -v htop &> /dev/null; then
    MISSING_DEPS+=("htop")
fi

# Install missing dependencies
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Installing missing dependencies: ${MISSING_DEPS[*]}${NC}"
    sudo apt update
    sudo apt install -y "${MISSING_DEPS[@]}"
else
    echo -e "${GREEN}✓ All dependencies satisfied${NC}"
fi

# Check for Pillow (PIL) for heightmap_to_watermap
echo -e "${YELLOW}Checking Pillow dependency for heightmap-to-watermap...${NC}"
if ! python3 -c "import PIL" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python Pillow library...${NC}"
    pip3 install --user Pillow
else
    echo -e "${GREEN}✓ Pillow already installed${NC}"
fi

# Create wrapper scripts
INSTALLED_COMMANDS=()
for script_info in "${SCRIPTS[@]}"; do
    IFS=':' read -r script_path command_name <<< "$script_info"
    wrapper_path="$USER_BIN_DIR/$command_name"
    
    # Check if command already exists
    if [ -f "$wrapper_path" ]; then
        echo -e "${YELLOW}Command '$command_name' already exists. Updating...${NC}"
    fi
    
    # Create wrapper script
    cat > "$wrapper_path" << EOF
#!/bin/bash
# Auto-generated wrapper for $command_name
# Part of PS-Utils Command Toolkit

python3 "$script_path" "\$@"
EOF
    
    chmod +x "$wrapper_path"
    INSTALLED_COMMANDS+=("$command_name")
    echo -e "${GREEN}✓ Installed: $command_name${NC}"
done

# Special setup for touch-log-viewer on Raspberry Pi
echo -e "${CYAN}Setting up touch-log-viewer for Raspberry Pi...${NC}"

# Check if user is in input group (needed for touch device access)
if ! groups "$USER" | grep -q "input"; then
    echo -e "${YELLOW}Adding user to 'input' group for touchscreen access...${NC}"
    sudo usermod -a -G input "$USER"
    echo -e "${YELLOW}⚠️  You need to log out and log back in for group changes to take effect${NC}"
fi

# Create a desktop entry for touch-log-viewer (if running on Pi with desktop)
if [ -n "$DISPLAY" ] && [ -d "$HOME/Desktop" ]; then
    DESKTOP_FILE="$HOME/Desktop/touch-log-viewer.desktop"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Touch Log Viewer
Comment=Touch-controlled log monitoring for Raspberry Pi
Exec=$USER_BIN_DIR/touch-log-viewer
Icon=utilities-system-monitor
Terminal=true
Categories=System;Monitor;
EOF
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}✓ Created desktop shortcut for touch-log-viewer${NC}"
fi

# Create uninstall script
UNINSTALL_SCRIPT="$SCRIPT_DIR/uninstall_linux.sh"
cat > "$UNINSTALL_SCRIPT" << 'EOF'
#!/bin/bash
# Uninstall script for PS-Utils Linux installation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_BIN_DIR="$HOME/.local/bin"
PROFILE_FILE="$HOME/.bashrc"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}PS-Utils Uninstaller${NC}"
echo "===================="

# Commands to remove
COMMANDS=(
EOF

# Add commands to uninstall script
for script_info in "${SCRIPTS[@]}"; do
    IFS=':' read -r script_path command_name <<< "$script_info"
    echo "    \"$command_name\"" >> "$UNINSTALL_SCRIPT"
done

cat >> "$UNINSTALL_SCRIPT" << 'EOF'
)

# Remove command wrappers
for cmd in "${COMMANDS[@]}"; do
    if [ -f "$USER_BIN_DIR/$cmd" ]; then
        rm "$USER_BIN_DIR/$cmd"
        echo -e "${GREEN}✓ Removed: $cmd${NC}"
    else
        echo -e "${YELLOW}⚠ Not found: $cmd${NC}"
    fi
done

# Remove desktop file
if [ -f "$HOME/Desktop/touch-log-viewer.desktop" ]; then
    rm "$HOME/Desktop/touch-log-viewer.desktop"
    echo -e "${GREEN}✓ Removed desktop shortcut${NC}"
fi

# Ask if user wants to remove PATH modification
echo -e "${YELLOW}Do you want to remove the PATH modification from $PROFILE_FILE? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    # Remove the PS-Utils PATH addition
    if grep -q "# Added by PS-Utils setup" "$PROFILE_FILE"; then
        # Create a temporary file without the PS-Utils lines
        grep -v "# Added by PS-Utils setup" "$PROFILE_FILE" | \
        grep -v 'export PATH="$HOME/.local/bin:$PATH"' > "$PROFILE_FILE.tmp"
        mv "$PROFILE_FILE.tmp" "$PROFILE_FILE"
        echo -e "${GREEN}✓ Removed PATH modification${NC}"
    fi
fi

echo -e "${GREEN}Uninstallation complete!${NC}"
echo "Note: Dependencies (tmux, multitail, htop, python3-evdev) were not removed."
echo "You can remove them manually if needed: sudo apt remove tmux multitail htop python3-evdev"
EOF

chmod +x "$UNINSTALL_SCRIPT"

echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo -e "${CYAN}Installed commands:${NC}"
for cmd in "${INSTALLED_COMMANDS[@]}"; do
    echo -e "  ${GREEN}• $cmd${NC}"
done
echo ""
echo -e "${YELLOW}Important notes for Raspberry Pi:${NC}"
echo -e "  • ${YELLOW}Log out and log back in to use touchscreen features${NC}"
echo -e "  • ${YELLOW}Source your .bashrc or start a new terminal: source ~/.bashrc${NC}"
echo -e "  • ${YELLOW}For touch-log-viewer, ensure you have appropriate log files or modify the script${NC}"
echo ""
echo -e "${CYAN}Usage examples:${NC}"
echo -e "  combine-files /path/to/project output.txt --include '*.py'"
echo -e "  heightmap-to-watermap input.png output.png --min-depth 0 --max-depth 100"
echo -e "  touch-log-viewer  # (requires touchscreen and log files)"
echo ""
echo -e "${YELLOW}To uninstall: $UNINSTALL_SCRIPT${NC}"
echo ""
echo -e "${GREEN}Enjoy your PS-Utils toolkit on Raspberry Pi OS! 🥧${NC}"
