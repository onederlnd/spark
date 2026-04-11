#!/bin/bash
# check-domain.sh — Domain diagnostic for go-spark.app
# Usage: bash check-domain.sh

DOMAIN="go-spark.app"
WWW="www.go-spark.app"
FLY_APP="social-platform"
IPV4="66.241.124.244"
IPV6="2a09:8280:1::ec:a73b:0"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}  ✓ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
header() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   go-spark.app Diagnostic Script     ║"
echo "╚══════════════════════════════════════╝"

# ── DNS ─────────────────────────────────────────────────────────────────────
header "DNS Records"

RESOLVED_A=$(dig +short A $DOMAIN @8.8.8.8 2>/dev/null | head -1)
if [ "$RESOLVED_A" = "$IPV4" ]; then
  pass "A record → $RESOLVED_A"
elif [ -z "$RESOLVED_A" ]; then
  fail "A record missing (expected $IPV4)"
else
  fail "A record → $RESOLVED_A (expected $IPV4)"
fi

RESOLVED_AAAA=$(dig +short AAAA $DOMAIN @8.8.8.8 2>/dev/null | head -1)
if [ "$RESOLVED_AAAA" = "$IPV6" ]; then
  pass "AAAA record → $RESOLVED_AAAA"
elif [ -z "$RESOLVED_AAAA" ]; then
  fail "AAAA record missing (expected $IPV6)"
else
  fail "AAAA record → $RESOLVED_AAAA (expected $IPV6)"
fi

WWW_CNAME=$(dig +short CNAME $WWW @8.8.8.8 2>/dev/null | head -1)
if echo "$WWW_CNAME" | grep -q "go-spark.app"; then
  pass "www CNAME → $WWW_CNAME"
else
  fail "www CNAME missing or wrong → '$WWW_CNAME'"
fi

# ── SSL ──────────────────────────────────────────────────────────────────────
header "SSL Certificates"

check_ssl() {
  local host=$1
  CERT_INFO=$(echo | openssl s_client -connect $host:443 -servername $host 2>/dev/null)
  
  EXPIRY=$(echo "$CERT_INFO" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  ISSUER=$(echo "$CERT_INFO" | openssl x509 -noout -issuer 2>/dev/null | grep -o "O=[^,]*" | head -1)
  CHAIN=$(echo "$CERT_INFO" | grep -c "certificate")

  if [ -z "$EXPIRY" ]; then
    fail "$host — could not retrieve cert"
    return
  fi

  EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY" +%s 2>/dev/null)
  NOW_EPOCH=$(date +%s)
  DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

  if [ "$DAYS_LEFT" -gt 14 ]; then
    pass "$host — cert valid, expires in ${DAYS_LEFT} days ($ISSUER)"
  elif [ "$DAYS_LEFT" -gt 0 ]; then
    warn "$host — cert expires in ${DAYS_LEFT} days — renew soon!"
  else
    fail "$host — cert EXPIRED"
  fi

  if [ "$CHAIN" -ge 2 ]; then
    pass "$host — cert chain looks complete"
  else
    fail "$host — incomplete cert chain (missing intermediates?)"
  fi
}

check_ssl $DOMAIN
check_ssl $WWW

# ── HTTP Responses ───────────────────────────────────────────────────────────
header "HTTP Responses"

check_http() {
  local url=$1
  local expect_redirect=$2

  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}|%{redirect_url}" --max-time 10 "$url")
  CODE=$(echo $RESPONSE | cut -d'|' -f1)
  REDIRECT=$(echo $RESPONSE | cut -d'|' -f2)

  if [ "$expect_redirect" = "true" ]; then
    if [ "$CODE" = "301" ] || [ "$CODE" = "302" ]; then
      pass "$url → $CODE redirect to $REDIRECT"
    else
      fail "$url → $CODE (expected 301 redirect to $DOMAIN)"
    fi
  else
    if [ "$CODE" = "200" ]; then
      pass "$url → 200 OK"
    elif [ "$CODE" = "000" ]; then
      fail "$url → no response (timeout or unreachable)"
    else
      fail "$url → $CODE"
    fi
  fi
}

check_http "https://$DOMAIN" false
check_http "https://$WWW" true
check_http "http://$DOMAIN" true      # should redirect to https
check_http "http://$WWW" true         # should redirect to https

# ── Fly.io App Status ────────────────────────────────────────────────────────
header "Fly.io App Status"

if command -v fly &>/dev/null; then
  FLY_STATUS=$(fly status -a $FLY_APP 2>&1)
  if echo "$FLY_STATUS" | grep -q "started"; then
    pass "Machine is running"
  else
    fail "Machine may be down"
    echo "$FLY_STATUS" | grep -E "STATE|REGION"
  fi

  CERTS=$(fly certs list -a $FLY_APP 2>&1)
  if echo "$CERTS" | grep -q "Issued"; then
    pass "Fly cert issued for $DOMAIN"
  else
    fail "Fly cert not issued — run: fly certs add $DOMAIN -a $FLY_APP"
  fi
  if echo "$CERTS" | grep -q "$WWW.*Issued"; then
    pass "Fly cert issued for $WWW"
  else
    warn "Fly cert for $WWW may not be issued — run: fly certs add $WWW -a $FLY_APP"
  fi
else
  warn "fly CLI not found — skipping Fly.io checks"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Done. Fix any ✗ items above."
echo "For DNS propagation: https://dnschecker.org/#A/$DOMAIN"
echo "For SSL detail:      https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""