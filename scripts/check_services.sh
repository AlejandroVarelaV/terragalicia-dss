#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_url() {
  local name="$1"
  local url="$2"

  if curl -fsS "${url}" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} ${name} -> ${url}"
    return 0
  fi

  echo -e "${RED}[FAIL]${NC} ${name} -> ${url}"
  return 1
}

echo -e "${YELLOW}Checking TerraGalicia services...${NC}"

FAILURES=0

check_url "Orion" "http://localhost:1026/version" || FAILURES=$((FAILURES + 1))
check_url "QuantumLeap" "http://localhost:8668/version" || FAILURES=$((FAILURES + 1))
check_url "IoT Agent" "http://localhost:4041/iot/about" || FAILURES=$((FAILURES + 1))
check_url "Backend" "http://localhost:8000/api/v1/health" || FAILURES=$((FAILURES + 1))

if [[ "${FAILURES}" -gt 0 ]]; then
  echo -e "${RED}${FAILURES} service check(s) failed.${NC}"
  exit 1
fi

echo -e "${GREEN}All service checks passed.${NC}"
