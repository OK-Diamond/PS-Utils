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
    "combine-files"
    "heightmap-to-watermap"
    "pi-config"
    "touch-log-viewer"
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
