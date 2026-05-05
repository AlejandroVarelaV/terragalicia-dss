#!/bin/bash
set -u

BASE_URL="http://localhost"
PASS=0
FAIL=0

check() {
  local path=$1
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$path") || true
  if [[ "$code" =~ ^2 ]] || [[ "$code" == "401" ]]; then
    echo "PASS [$code] $path"
    PASS=$((PASS + 1))
  elif [[ "$code" =~ ^3 ]]; then
    echo "WARN [$code] $path"
    PASS=$((PASS + 1))
  else
    echo "FAIL [$code] $path"
    FAIL=$((FAIL + 1))
  fi
}

check "/"
check "/api/v1/health"
check "/api/v1/docs"
check "/api/v1/parcels"
check "/api/v1/farms"
check "/api/v1/crops"

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -eq 0 ]; then
  exit 0
else
  exit 1
fi
