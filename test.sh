#!/bin/bash

set -e

CLIENT_PID=""

cleanup() {
    echo "--- Cleanup handler running ---"
    # Check if CLIENT_PID has been set and if the process actually exists
    if [ -n "$CLIENT_PID" ] && ps -p $CLIENT_PID > /dev/null; then
        echo "--- Cleaning up Test Client (PID: $CLIENT_PID) ---"
        kill $CLIENT_PID
        wait $CLIENT_PID 2>/dev/null
        echo "--- Client cleaned up ---"
    else
        echo "--- No client process to clean up ---"
    fi
}

trap cleanup EXIT INT TERM

RELIABLE_MODE=$1

if [ -z "$RELIABLE_MODE" ]; then
    echo "Usage: $0 <reliable_mode> <test_name>"
    echo "  <reliable_mode> can be: reliable/r or unreliable/u"
    exit 1
fi

if [ "$RELIABLE_MODE" = "cleanup" ]; then
    echo "--- Cleaning up network rules ---"
    bash tests/setup_netem.sh cleanup
    exit 0
fi

TEST_NAME=$2

if [ -z "$TEST_NAME" ]; then
    echo "Usage: $0 $1 <test_name>"
    echo "  <test_name> can be: low_loss, high_loss, or default"
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
    default)
        echo "--- Setting up DEFAULT (no loss, low latency) ---"
        bash tests/setup_netem.sh default
        ;;
    *)
        echo "Invalid test name. Use 'low_loss', 'high_loss', or 'default'."
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

TEST_EXIT_CODE=0

if [ "$RELIABLE_MODE" == "reliable" ] || [ "$RELIABLE_MODE" == "r" ]; then
    echo "--- Running in RELIABLE mode ---"
    echo "--- Starting Test Server (in background) for reliable data transfer ---"
    exec 3> >(tee "$LOG_DIR/server_r.log")
    python3 -u -m tests.test_server_r >&3 2>&3 &
    SERVER_PID=$!
    exec 3>&- # Close file descriptor

    # Give server time to bind and listen
    sleep 1

    echo "--- Running Test Client (in background) ---"
    python3 -u -m tests.test_client_r > "$LOG_DIR/client_r.log" 2>&1 &
    CLIENT_PID=$!

elif [ "$RELIABLE_MODE" == "unreliable" ] || [ "$RELIABLE_MODE" == "u" ]; then
    echo "--- Running in UNRELIABLE mode ---"
    echo "--- Starting Test Server (in background) for unreliable data transfer ---"
    exec 3> >(tee "$LOG_DIR/server_u.log")
    python3 -u -m tests.test_server_u >&3 2>&3 &
    SERVER_PID=$!
    exec 3>&-

    sleep 1

    echo "--- Running Test Client (in background) ---"
    python3 -u -m tests.test_client_u > "$LOG_DIR/client_u.log" 2>&1 &
    CLIENT_PID=$!

elif [ "$RELIABLE_MODE" == "ur" ] || [ "$RELIABLE_MODE" == "mixed" ]; then
    echo "--- Running in mixed RELIABLE and UNRELIABLE mode ---"
    echo "--- Starting Test Server (in background) for mixed data transfer ---"
    exec 3> >(tee "$LOG_DIR/server_ur.log")
    python3 -u -m tests.test_server_ur >&3 2>&3 &
    SERVER_PID=$!
    exec 3>&-

    sleep 1

    echo "--- Running Test Client (in background) ---"
    python3 -u -m tests.test_client_ur > "$LOG_DIR/client_ur.log" 2>&1 &
    CLIENT_PID=$!

else
    echo "Invalid reliable mode. Use 'reliable/r', 'unreliable/u', or 'mixed/ur'."
    exit 1
fi


echo "--- Waiting for Test Server (PID: $SERVER_PID) to complete... ---"
set +e
wait $SERVER_PID
TEST_EXIT_CODE=$?
set -e
echo "--- Test Server finished with exit code $TEST_EXIT_CODE ---"


if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "--- RESULT: ALL TESTS PASSED ---"
else
    echo "--- RESULT: TESTS FAILED (Exit Code: $TEST_EXIT_CODE) ---"
fi

#    This makes the script fail if the Python test fails.
exit $TEST_EXIT_CODE

