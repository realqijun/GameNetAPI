#!/bin/sh

# Set variables
TEST_NAME=$1
TEST_DIR="tests/"

if [ -z "$TEST_NAME" ]; then
    echo "Usage: $0 <test_name>"
    exit 1
fi

case "$TEST_NAME" in
    low_loss)
        bash tests/setup_netem.sh low_loss
        ;;
    high_loss)
        bash tests/setup_netem.sh high_loss
        ;;
    cleanup)
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
echo "Installing requirements..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements."
    exit 1
fi

echo "Starting server..."
python3 "${TEST_DIR}test_server.py" &
SERVER_PID=$!

sleep 1

echo "Running client..."
python3 "${TEST_DIR}test_client.py"
CLIENT_EXIT_CODE=$? # Capture the client's exit code

echo "Cleaning up server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

#    This makes the script fail if the Python test fails.
exit $CLIENT_EXIT_CODE