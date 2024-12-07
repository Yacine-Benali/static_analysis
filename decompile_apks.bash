#!/bin/bash

# Define the input and output directories
APK_DIR="./APKs"
SMALI_DIR="./SMALI"

# Create the SMALI directory if it doesn't exist
mkdir -p "$SMALI_DIR"

# Loop through all APK files in the APK_DIR
for apk in "$APK_DIR"/*.apk; do
    # Extract the base name of the APK file (without the .apk extension)
    apk_name=$(basename "$apk" .apk)
    
    # Define the output directory for this APK's smali code
    output_dir="$SMALI_DIR/$apk_name"
    
    # Create the output directory
    mkdir -p "$output_dir"
    
    # Decompile the APK with apktool into the output directory
    apktool d "$apk" -o "$output_dir" -f
    
    echo "Decompiled $apk into $output_dir"
done
