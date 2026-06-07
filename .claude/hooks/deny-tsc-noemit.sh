#!/usr/bin/env bash
# Block direct `tsc --noEmit` invocations; canonicalize on `make typecheck`.

input=$(cat)
command=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if echo "$command" | grep -qE 'tsc[[:space:]].*--noEmit|--noEmit[[:space:]].*tsc'; then
  echo '{"decision":"block","reason":"Use `make typecheck` instead of calling tsc --noEmit directly."}'
  exit 0
fi
