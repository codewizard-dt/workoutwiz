#!/bin/bash
# PostToolUse hook: fires after Edit or Write tool use.
# If the modified file is under frontend/src/pages/, injects the brand skill
# into Claude's active context so design rules are always in scope.
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('file_path', d.get('path', '')))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [[ "$FILE_PATH" =~ ^.*\.tsx$ ]]; then
  ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  SKILL="$ROOT/.claude/skills/workout-wiz-brand-design/SKILL.md"
  if [ -f "$SKILL" ]; then
    echo ""
    echo "=== WORKOUT WIZ DESIGN SYSTEM ==="
    cat "$SKILL"
    echo "=================================="
  fi
fi
