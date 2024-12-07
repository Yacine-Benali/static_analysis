#!/bin/bash

# Paths (Modify these paths according to your environment)
FLOWDROID_JAR="../soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
PLATFORMS_DIR="../tools"
SOURCES_AND_SINKS="../SourcesAndSinks.txt"
APK_DIR="../APKs"

# Concurrency limit
MAX_JOBS=2

# Timeout settings in minutes
TIMEOUT_MINUTES_LIST=(1 5 20)

# Create an array of APK files in the APK_DIR
APK_FILES=("$APK_DIR"/*.apk)


# Track how many background jobs are running
RUNNING_JOBS=0

for APK_PATH in "${APK_FILES[@]}"; do
    # Extract the APK filename without the directory path
    APK_FILENAME=$(basename "$APK_PATH")
    # Remove the .apk extension to get the base name
    APK_NAME="${APK_FILENAME%.apk}"

    # Loop over each timeout setting
    for TIMEOUT_MINUTES in "${TIMEOUT_MINUTES_LIST[@]}"; do
        # Output and log file names
        OUTPUT_FILE="./${APK_NAME}-${TIMEOUT_MINUTES}min.xml"
        LOG_FILE="./${APK_NAME}-${TIMEOUT_MINUTES}min.log"
        # Convert timeout from minutes to seconds
        TIMEOUT_SECONDS=$((TIMEOUT_MINUTES * 60))

        echo "Analyzing ${APK_FILENAME} with a timeout of ${TIMEOUT_MINUTES} minutes (${TIMEOUT_SECONDS} seconds)..."

        # Run FlowDroid analysis in the background
        java -Xms8G -jar "$FLOWDROID_JAR" --aliasflowins --aplength 1 --noexceptions --nostatic  \
            -a "$APK_PATH" \
            -p "$PLATFORMS_DIR" \
            -s "$SOURCES_AND_SINKS" \
            -dt "$TIMEOUT_SECONDS" -rt "$TIMEOUT_SECONDS" -ct "$TIMEOUT_SECONDS" \
            -o "$OUTPUT_FILE" &> "${LOG_FILE}" &

        # Increment the count of running jobs
        RUNNING_JOBS=$((RUNNING_JOBS + 1))

        # If we reached the max concurrency, wait for one job to finish
        if [ $RUNNING_JOBS -ge $MAX_JOBS ]; then
            wait -n  # wait for one of the background jobs to finish
            RUNNING_JOBS=$((RUNNING_JOBS - 1))
        fi

    done
done

# Wait for any remaining jobs to complete
wait

echo "All analyses completed."
