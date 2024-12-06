#!/bin/bash

# Paths (Modify these paths according to your environment)
FLOWDROID_JAR="soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
PLATFORMS_DIR="./tools"
SOURCES_AND_SINKS="./SourcesAndSinks.txt"
APK_DIR="./APKs"

##############################""
# com.hawai 20min i stopped manually cause it took over 20min



# Timeout settings in minutes
TIMEOUT_MINUTES=(1 5 20)

# Create an array of APK files in the APK_DIR
APK_FILES=("$APK_DIR"/*.apk)

# Loop over each APK file
for APK_PATH in "${APK_FILES[@]}"; do
    # Extract the APK filename without the directory path
    APK_FILENAME=$(basename "$APK_PATH")
    # Remove the .apk extension to get the base name
    APK_NAME="${APK_FILENAME%.apk}"

    # Loop over each timeout setting
    for TIMEOUT_MINUTES in "${TIMEOUT_MINUTES[@]}"; do
        # Output file name
        OUTPUT_FILE="./outputs/${APK_NAME}-${TIMEOUT_MINUTES}min.xml"
        LOG_FILE="./outputs/${APK_NAME}-${TIMEOUT_MINUTES}min.log"
        # Convert timeout from minutes to seconds
        TIMEOUT_SECONDS=$((TIMEOUT_MINUTES * 60))

        echo "Analyzing ${APK_FILENAME} with a timeout of ${TIMEOUT_MINUTES} minutes (${TIMEOUT_SECONDS} seconds)..."

        # Run FlowDroid analysis and save the output to the file
        java -jar "$FLOWDROID_JAR" \
            -a "$APK_PATH" \
            -p "$PLATFORMS_DIR" \
            -s "$SOURCES_AND_SINKS" \
            -dt "$TIMEOUT_SECONDS" -rt "$TIMEOUT_SECONDS" -ct "$TIMEOUT_SECONDS" \
            -o "$OUTPUT_FILE" &> "${LOG_FILE}"

        echo "Output saved to ${OUTPUT_FILE}"
        echo "---------------------------------------------"
    done
done

echo "All analyses completed."
