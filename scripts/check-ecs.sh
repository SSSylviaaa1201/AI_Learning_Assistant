#!/usr/bin/env bash
set -eu
umask 077
ECS_PUBLIC_IP="${1:?Usage: bash scripts/check-ecs.sh ECS_PUBLIC_IP}"
case "$ECS_PUBLIC_IP" in *[!0-9.]*) echo 'Expected an IPv4 address' >&2; exit 2;; esac
{
  printf 'AI Learning Assistant ECS Web Interface Check\n'
  date '+Time (local): %Y-%m-%dT%H:%M:%S%z'
  date -u '+Time (UTC): %Y-%m-%dT%H:%M:%SZ'
  printf 'Machine: %s\n' "$(hostname)"
  printf 'Operating system: %s\n' "$(uname -sr)"
  printf 'CPU architecture: %s\n' "$(uname -m)"
  printf 'ECS login user: %s\n' "$(whoami)"
  printf 'Website URL: http://%s:14242/ui/\n' "$ECS_PUBLIC_IP"
  docker --version
  printf '\nDocker application container:\n'
  docker ps -a --filter publish=14242 --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
  printf '\nHealth check:\n'
  curl --noproxy '*' -fsS http://127.0.0.1:14242/health
  printf '\nWebsite URL check from ECS:\n'
  status=$(curl --noproxy '*' -sS --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}' "http://${ECS_PUBLIC_IP}:14242/ui/" || true)
  printf 'HTTP status: %s\n' "$status"
  if [ "$status" = 200 ]; then
    printf 'Website URL check: PASS\n'
  else
    printf 'Website URL check: FAIL (check security group source restrictions)\n'
  fi
} 2>&1 | tee ecs-docker-check.txt
