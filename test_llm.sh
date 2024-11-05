#!/bin/sh

# test_llm.sh - Test script for LLM server endpoint

# Load environment variables
if [ -f .env ]; then
    set -o allexport
    source ./.env
    set +o allexport
else
    echo "Error: .env file not found"
    exit 1
fi

# Verify required variables
if [ -z "$INSTANCE_NAME" ] || [ -z "$ZONE" ] || [ -z "$PORT" ]; then
    echo "Error: Required environment variables not set"
    echo "Please ensure INSTANCE_NAME, ZONE, and PORT are set in .env"
    exit 1
fi

# Fetch the external IP address of the instance
echo "Getting instance IP for $INSTANCE_NAME in $ZONE..."
INSTANCE_IP=$(gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

if [ -z "$INSTANCE_IP" ]; then
    echo "Error: Could not get instance IP"
    exit 1
fi

echo "Instance IP: $INSTANCE_IP"

# Read user queries in a loop
echo -e "\nEnter your queries (type 'q' to quit):"

while true; do
    echo -e "\nQuery > "
    read -r query

    if [ "$query" = "q" ]; then
        echo "Goodbye!"
        break
    fi

    if [ -n "$query" ]; then
        echo -e "\nSending request to LLM server..."
        
        # Escape quotes in the query
        escaped_query=$(echo "$query" | sed 's/"/\\"/g')

        # Send request and get response
        response=$(curl -s -X POST "http://$INSTANCE_IP:$PORT/generate/" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"$escaped_query\", \"max_length\": 100}")

        # Check for errors
        if [ $? -ne 0 ]; then
            echo "Error: Failed to connect to server"
        else
            # Parse response using sed to extract generated text
            generated_text=$(echo "$response" | sed 's/.*"generated_text":"\([^"]*\)".*/\1/')
            echo -e "\nResponse: $generated_text"
        fi
    fi
done
