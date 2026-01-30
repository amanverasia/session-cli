#!/bin/bash
# Launch Session with CDP (Chrome DevTools Protocol) enabled
# This allows Python to control Session programmatically

# Kill existing Session if running
pkill -x "Session" 2>/dev/null
sleep 1

# Launch with remote debugging
echo "Starting Session with CDP enabled on port 9222..."
/Applications/Session.app/Contents/MacOS/Session \
    --remote-debugging-port=9222 \
    --remote-allow-origins="*" &

echo "Session started! CDP available at http://localhost:9222"
echo ""
echo "Test with: curl http://localhost:9222/json"
