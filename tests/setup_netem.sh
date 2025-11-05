#!/bin/bash

# USAGE:
#   1. Set interface to 'lo' for testing on localhost, or 'eth0'/'wlan0' for remote testing.
#   2. Run: ./setup_netem.sh [condition]
#   3. Example: ./setup_netem.sh low_loss
#   4. To clean up: ./setup_netem.sh cleanup

# --- CONFIGURATION ---
IFACE="lo" # Interface to apply rules to (change to eth0, wlan0, etc. as needed)


# Function to add the rule
add_rule() {
    CONDITION=$1
    echo "--- Configuring H-UDP Test Condition: $CONDITION on $IFACE ---"

    # Check if a rule already exists and delete it first
    sudo tc qdisc del dev "$IFACE" root 2> /dev/null

    if [ "$CONDITION" == "low_loss" ]; then
        # Condition 1: Low Loss/Low Latency
        # - Delay: 50ms average, +/- 5ms jitter
        # - Loss: 5%
        echo "Applying: Delay=50ms (5ms jitter), Loss=1%"
        sudo tc qdisc add dev "$IFACE" root netem delay 50ms 5ms distribution normal loss 5%

    elif [ "$CONDITION" == "high_loss" ]; then
        # Condition 2: High Loss/High Latency
        # - Delay: 100ms average, +/- 20ms jitter
        # - Loss: 25%
        echo "Applying: Delay=100ms (20ms jitter), Loss=12%"
        sudo tc qdisc add dev "$IFACE" root netem delay 100ms 20ms distribution normal loss 25%

    elif [ "$CONDITION" == "cleanup" ]; then
        echo "Removing all tc-netem rules from $IFACE..."
        # Deleting the root rule removes all child rules
        sudo tc qdisc del dev "$IFACE" root 2> /dev/null
        echo "Cleanup complete."

    else
        echo "ERROR: Invalid condition argument. Use 'low_loss', 'high_loss', or 'cleanup'."
        exit 1
    fi

    # Verify configuration (optional)
    if [ "$CONDITION" != "cleanup" ]; then
        echo "Current configuration:"
        tc qdisc show dev "$IFACE"
    fi
}

# --- MAIN EXECUTION ---
if [ "$#" -ne 1 ]; then
    echo "Usage: ./setup_netem.sh [low_loss | high_loss | cleanup]"
    exit 1
fi

add_rule "$1"
