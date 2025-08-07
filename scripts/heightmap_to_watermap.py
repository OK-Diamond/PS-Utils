#!/usr/bin/env python3
"""
heightmap_to_watermap.py - Convert heightmap to water colormap for EU4 map modding

This script takes a heightmap image and generates a water colormap where the color
depends on the height value. Darker areas in the heightmap will be colored as deeper
water (darker blue), while lighter areas will be shallow water (lighter blue).

Usage:
    heightmap_to_watermap.py input_heightmap.png output_watermap.png [--min-depth MIN] [--max-depth MAX]
"""

import argparse
import os
import sys
from PIL import Image
import numpy as np

def heightmap_to_watermap(input_path, output_path, min_depth=0, max_depth=255):
    """
    Convert a heightmap to a water colormap for EU4.
    
    Args:
        input_path: Path to the input heightmap image
        output_path: Path for the output watermap image
        min_depth: Minimum depth value (0-255)
        max_depth: Maximum depth value (0-255)
    """
    # Open and convert the heightmap to grayscale
    heightmap = Image.open(input_path).convert('L')
    height_array = np.array(heightmap)

    # Create output image with same dimensions as input
    width, height = heightmap.size
    watermap = Image.new('RGB', (width, height))
    watermap_data = []

    # Define water color range (dark blue to light blue)
    deep_water = (10, 30, 120)    # Dark blue for deep water
    shallow_water = (80, 170, 220)  # Light blue for shallow water

    # Process each pixel
    for y in range(height):
        for x in range(width):
            # Get the height value (0-255)
            height_value = height_array[y, x]

            # Skip values outside the specified range
            if height_value < min_depth or height_value > max_depth:
                # Use land color (beige) for non-water areas
                watermap_data.append((230, 220, 190))
                continue

            # Normalize the height value within the specified range
            normalized = (height_value - min_depth) / (max_depth - min_depth)

            # Interpolate between deep and shallow water colors
            r = int(deep_water[0] + normalized * (shallow_water[0] - deep_water[0]))
            g = int(deep_water[1] + normalized * (shallow_water[1] - deep_water[1]))
            b = int(deep_water[2] + normalized * (shallow_water[2] - deep_water[2]))

            watermap_data.append((r, g, b))

    # Set the pixel data and save the image
    watermap.putdata(watermap_data)
    watermap.save(output_path)

    print(f"Successfully converted {input_path} to water colormap at {output_path}")
    return True

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Convert a heightmap to a water colormap for EU4 map modding"
    )
    parser.add_argument("input", help="Path to the input heightmap image")
    parser.add_argument("output", help="Path for the output water colormap image")
    parser.add_argument(
        "--min-depth",
        type=int,
        default=0,
        help="Minimum height value to be considered as water (0-255, default: 0)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=100,
        help="Maximum height value to be considered as water (0-255, default: 100)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    if args.min_depth < 0 or args.min_depth > 255:
        print("Error: min-depth must be between 0 and 255.")
        sys.exit(1)

    if args.max_depth < 0 or args.max_depth > 255:
        print("Error: max-depth must be between 0 and 255.")
        sys.exit(1)

    if args.min_depth >= args.max_depth:
        print("Error: min-depth must be less than max-depth.")
        sys.exit(1)

    # Run the conversion
    success = heightmap_to_watermap(
        args.input, 
        args.output, 
        args.min_depth, 
        args.max_depth
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
