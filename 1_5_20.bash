#!/bin/bash


# Paths (Modify these paths according to your environment)
FLOWDROID_JAR="soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
PLATFORMS_DIR="./tools"
SOURCES_AND_SINKS="./SourcesAndSinks.txt"
APK_DIR="./APKs"

# Timeout settings in minutes
TIMEOUTS=(1 5 20)

# Create an array of APK files in the APK_DIR
APK_FILES=("$APK_DIR"/*.apk)

# Loop over each APK file
for APK_PATH in "${APK_FILES[@]}"; do
    # Extract the APK filename without the directory path
    APK_FILENAME=$(basename "$APK_PATH")
    # Remove the .apk extension to get the base name
    APK_NAME="${APK_FILENAME%.apk}"

    # Loop over each timeout setting
    for TIMEOUT in "${TIMEOUTS[@]}"; do
        # Output file name
        OUTPUT_FILE="./outputs/${APK_NAME}-${TIMEOUT}min.xml"

        echo "Analyzing ${APK_FILENAME} with a timeout of ${TIMEOUT} minute(s)..."

        # Run FlowDroid analysis and save the output to the file
        java -jar "$FLOWDROID_JAR" \
            -a "$APK_PATH" \
            -p "$PLATFORMS_DIR" \
            -s "$SOURCES_AND_SINKS" \
            -dt "$TIMEOUT" -rt "$TIMEOUT" -ct "$TIMEOUT" \
            -o "$OUTPUT_FILE" &> "${OUTPUT_FILE}.log"

        echo "Output saved to ${OUTPUT_FILE}"
        echo "---------------------------------------------"
    done
done

echo "All analyses completed."
