#!/bin/sh

# Set variables
TEST_NAME=$1
TEST_DIR="tests/"

if [ -z "$TEST_NAME" ]; then
    echo "Usage: $0 <test_name>"
    echo "  <test_name> can be: low_loss, high_loss, or cleanup"
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
    *)
        echo "Invalid test name. Use 'low_loss', 'high_loss', or 'cleanup'."
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
echo "Installing requirements (if any)..."
# pip3 install -r requirements.txt # Uncomment if you have a requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements."
    exit 1
fi

echo "--- Starting Test Server (in background) ---"
python3 -m tests.test_server &
SERVER_PID=$!

# Give server time to bind and listen
sleep 1

echo "--- Running Test Client (test driver) ---"
python3 -m tests.test_client
CLIENT_EXIT_CODE=$? # Capture the client's exit code

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

