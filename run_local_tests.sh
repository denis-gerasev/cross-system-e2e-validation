# Exit the script immediately if any command returns an error
set -e

cd react-shopping-cart

PORT=3000

# Cleanup function: kills the background npm on any script exit
cleanup() {
  if [ -n "$NPM_PID" ]; then
    echo "Stopping npm server (PID: $NPM_PID)..."
    kill "$NPM_PID" 2>/dev/null || true
    lsof -ti tcp:$PORT -sTCP:LISTEN | xargs -r kill -9 2>/dev/null || true
    wait "$NPM_PID" 2>/dev/null || true
  fi
}

# Cleanup function will execute on exit (EXIT),
# interruption (INT/Ctrl+C) or script termination (TERM)
trap cleanup EXIT INT TERM

# Check if dependencies are installed before starting
if [ ! -f node_modules/.bin/react-scripts ]; then
  echo "react-scripts missing. Installing dependencies..."
  npm install --legacy-peer-deps
fi

# Kill any leftover server listening on $PORT from previous runs
lsof -ti tcp:$PORT -sTCP:LISTEN | xargs -r kill -9 2>/dev/null || true

echo "Starting npm server"
# Start in background (&) and redirect output, so server logs don't mix with test output

npm start > npm_server.log 2>&1 &
NPM_PID=$!

echo "Waiting for $PORT to become ready..."
# Loop checks the port's availability (requires nc or curl)
while ! nc -z localhost $PORT >/dev/null 2>&1; do
  if ! kill -0 $NPM_PID 2>/dev/null; then
    echo "npm server failed to start! Check npm_server.log:"
    cat npm_server.log
    exit 1
  fi
  sleep 1
done

echo "Server is ready. Starting pytest..."
cd ../
# Disable 'set -e', so the script
# doesn't exit before cleanup call, if tests will fail
set +e
pytest --headed -s
TEST_EXIT_CODE=$?

# Return pytest's exit code, so CI/CD knows whether the tests passed
exit $TEST_EXIT_CODE