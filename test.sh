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

RELIABLE_MODE=$1

if [ -z "$RELIABLE_MODE" ]; then
    echo "Usage: $0 <reliable_mode> <test_name>"
    echo "  <reliable_mode> can be: reliable/r or unreliable/u"
    exit 1
fi

TEST_NAME=$2

if [ -z "$TEST_NAME" ]; then
    echo "Usage: $0 $1 <test_name>"
    echo "  <test_name> can be: low_loss, high_loss, cleanup, or default"
    exit 1
fi

case "$TEST_NAME" in
    low_loss)
        echo "--- Setting up LOW LOSS (1%) and LOW LATENCY (50ms) ---"
        bash tests/setup_netem.sh low_loss
        ;;
    high_loss)
        echo "--- Setting up HIGH LOSS (12%) and HIGH LATENCY (100ms) ---"
        bash tests/setup_netem.sh high_loss
        ;;
    cleanup)
        echo "--- Cleaning up network rules ---"
        bash tests/setup_netem.sh cleanup
        exit 0
        ;;
    default)
        echo "--- Setting up DEFAULT (no loss, low latency) ---"
        bash tests/setup_netem.sh default
        ;;
    *)
        echo "Invalid test name. Use 'low_loss', 'high_loss', 'cleanup', or 'default'."
        exit 1
        ;;
esac

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

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

if [ "$RELIABLE_MODE" == "reliable" ] || [ "$RELIABLE_MODE" == "r" ]; then
    echo "--- Running in RELIABLE mode ---"
    echo "--- Starting Test Server (in background) for reliable data transfer ---"
    python3 -u -m tests.test_server_r > "$LOG_DIR/server_r.log" 2>&1 &
    SERVER_PID=$!

    # Give server time to bind and listen
    sleep 1

    echo "--- Running Test Client (test driver) for reliable data transfer ---"
    set +e
    python3 -u -m tests.test_client_r 2>&1 | tee "$LOG_DIR/client_r.log"
    CLIENT_EXIT_CODE=${PIPESTATUS[0]}
    set -e

elif [ "$RELIABLE_MODE" == "unreliable" ] || [ "$RELIABLE_MODE" == "u" ]; then
    echo "--- Running in UNRELIABLE mode ---"
    echo "--- Starting Test Server (in background) for unreliable data transfer ---"
    python3 -u -m tests.test_server_u > "$LOG_DIR/server_u.log" 2>&1 &
    SERVER_PID=$!

    # Give server time to bind and listen
    sleep 1

    echo "--- Running Test Client (test driver) for unreliable data transfer ---"
    set +e
    python3 -u -m tests.test_client_u 2>&1 | tee "$LOG_DIR/client_u.log"
    CLIENT_EXIT_CODE=${PIPESTATUS[0]}
    set -e

else
    echo "Invalid reliable mode. Use 'reliable/r' or 'unreliable/u'."
    exit 1
fi


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

