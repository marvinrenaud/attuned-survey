#!/bin/bash
# Backend API Endpoint Tester
# Tests all new recommendation and compatibility endpoints

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "Backend API Endpoint Tester"
echo "=================================="
echo ""
echo "Testing against: $BASE_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${YELLOW}Testing: $name${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo "$body" | jq -C '.' 2>/dev/null || echo "$body"
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "$body" | jq -C '.' 2>/dev/null || echo "$body"
        echo ""
        return 1
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not installed. Install with: brew install jq${NC}"
    echo ""
fi

# Test 1: Get submissions (existing endpoint - health check)
echo "==================================
Test 1: Health Check (Get Submissions)
=================================="
if ! test_endpoint "GET /api/survey/submissions" "GET" "/api/survey/submissions"; then
    echo -e "${RED}Backend is not responding! Make sure it's running on port 5001${NC}"
    echo "Start with: cd backend && source venv/bin/activate && python -m flask --app src.main run --port 5001"
    exit 1
fi

# Get submission IDs for testing
echo "Fetching submission IDs for testing..."
SUBMISSIONS=$(curl -s "$BASE_URL/api/survey/submissions")
SUBMISSION_A=$(echo "$SUBMISSIONS" | jq -r '.submissions[0].id // empty')
SUBMISSION_B=$(echo "$SUBMISSIONS" | jq -r '.submissions[1].id // empty')

if [ -z "$SUBMISSION_A" ] || [ -z "$SUBMISSION_B" ]; then
    echo -e "${RED}Error: Need at least 2 survey submissions to test recommendations${NC}"
    echo "Please complete the survey twice first, or load test data"
    exit 1
fi

echo -e "${GREEN}Using submissions:${NC}"
echo "  Player A: $SUBMISSION_A"
echo "  Player B: $SUBMISSION_B"
echo ""

# Test 2: Generate Recommendations (5 activities for speed)
echo "==================================
Test 2: Generate Recommendations (5 activities)
=================================="
RECOMMENDATIONS_PAYLOAD='{
  "player_a": {"submission_id": "'$SUBMISSION_A'"},
  "player_b": {"submission_id": "'$SUBMISSION_B'"},
  "session": {
    "rating": "R",
    "target_activities": 5,
    "activity_type": "random"
  }
}'

if test_endpoint "POST /api/recommendations" "POST" "/api/recommendations" "$RECOMMENDATIONS_PAYLOAD"; then
    # Extract session_id for later test
    SESSION_ID=$(curl -s -X POST "$BASE_URL/api/recommendations" \
        -H "Content-Type: application/json" \
        -d "$RECOMMENDATIONS_PAYLOAD" | jq -r '.session_id // empty')
    echo -e "${GREEN}Session created: $SESSION_ID${NC}"
    echo ""
fi

# Test 3: Calculate Compatibility
echo "==================================
Test 3: Calculate Compatibility
=================================="
COMPATIBILITY_PAYLOAD='{
  "submission_id_a": "'$SUBMISSION_A'",
  "submission_id_b": "'$SUBMISSION_B'"
}'

test_endpoint "POST /api/compatibility" "POST" "/api/compatibility" "$COMPATIBILITY_PAYLOAD"

# Test 4: Get Cached Compatibility
echo "==================================
Test 4: Get Cached Compatibility
=================================="
test_endpoint "GET /api/compatibility/:id_a/:id_b" "GET" "/api/compatibility/$SUBMISSION_A/$SUBMISSION_B"

# Test 5: Get Session Activities (if we have a session_id)
if [ ! -z "$SESSION_ID" ]; then
    echo "==================================
Test 5: Get Session Activities
=================================="
    test_endpoint "GET /api/recommendations/:session_id" "GET" "/api/recommendations/$SESSION_ID"
fi

# Summary
echo "==================================
Test Summary
=================================="
echo ""
echo -e "${GREEN}✓ All critical endpoints tested!${NC}"
echo ""
echo "Next steps:"
echo "  1. Import activities: python backend/scripts/import_activities.py your_file.csv"
echo "  2. Test with 25 activities (change target_activities to 25)"
echo "  3. Verify in Supabase Studio that tables are populated"
echo ""
echo "Backend is ready for frontend integration! 🚀"

