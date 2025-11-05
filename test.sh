#!/bin/bash

set -e

SERVER_PID=""

cleanup() {
    echo "--- Cleanup handler running ---"
    # Check if SERVER_PID has been set and if the process actually exists
    if [ -n "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null; then
        echo "--- Cleaning up Test Server (PID: $SERVER_PID) ---"
        kill $SERVER_PID
        wait $SERVER_PID 2>/dev/null
        echo "--- Server cleaned up ---"
    else
        echo "--- No server process to clean up ---"
    fi
}

trap cleanup EXIT INT TERM

TEST_NAME=$1

# if [ -z "$TEST_NAME" ]; then
#     echo "Usage: $0 <test_name>"
#     echo "  <test_name> can be: low_loss, high_loss, or cleanup"
#     exit 1
# fi

# case "$TEST_NAME" in
#     low_loss)
#         echo "--- Setting up LOW LOSS (1%) and LOW LATENCY (50ms) ---"
#         bash tests/setup_netem.sh low_loss
#         ;;
#     high_loss)
#         echo "--- Setting up HIGH LOSS (12%) and HIGH LATENCY (100ms) ---"
#         bash tests/setup_netem.sh high_loss
#         ;;
#     cleanup)
#         echo "--- Cleaning up network rules ---"
#         bash tests/setup_netem.sh cleanup
#         exit 0
#         ;;
#     *)
#         echo "Invalid test name. Use 'low_loss', 'high_loss', or 'cleanup'."
#         exit 1
#         ;;
# esac

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed or not in PATH."
    echo "It is required to create the virtual environment."
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found. Creating 'venv'..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

. venv/bin/activate
echo "Installing requirements..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements."
    exit 1
fi

echo "--- Starting Test Server (in background) ---"
python3 -u -m tests.test_server > server.log 2>&1 &
SERVER_PID=$!

# Give server time to bind and listen
sleep 1

echo "--- Running Test Client (test driver) ---"
set +e
python3 -u -m tests.test_client 2>&1 | tee client.log
CLIENT_EXIT_CODE=${PIPESTATUS[0]}
set -e

echo "--- Cleaning up Test Server (PID: $SERVER_PID) ---"
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

if [ $CLIENT_EXIT_CODE -eq 0 ]; then
    echo "--- RESULT: ALL TESTS PASSED ---"
else
    echo "--- RESULT: TESTS FAILED (Exit Code: $CLIENT_EXIT_CODE) ---"
fi

#    This makes the script fail if the Python test fails.
exit $CLIENT_EXIT_CODE

