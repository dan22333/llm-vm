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
INSTANCE_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "Instance IP: $INSTANCE_IP"

# Read user query
read -p "Enter your query (press Enter to submit): " query

# Construct JSON payload
json_payload=$(cat <<EOF
{
  "text": "$query",
  "max_length": 100
}
EOF
)

# Send request to LLM server
echo "Sending request to LLM server..."
response=$(curl -s -X POST "http://$INSTANCE_IP:8080/generate/" \
  -H "Content-Type: application/json" \
  -d "$json_payload")

# Check for errors in the response and display
if [ $? -ne 0 ]; then
    echo "Error occurred with the curl request."
else
    # Parse the response to extract the generated text without jq
    generated_text=$(echo "$response" | grep -o '"generated_text":"[^"]*"' | sed 's/"generated_text":"\(.*\)"/\1/')
    echo "Response from LLM server: $generated_text"
fi

echo "Request complete."
