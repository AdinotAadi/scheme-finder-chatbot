#!/usr/bin/env python3
"""Read-only Claude hook: remind agents to reconcile AI-DLC state and handover."""
import json
from pathlib import Path
import sys
import tempfile

def main():
    if '--self-test' in sys.argv:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'aidlc-docs' / 'aidlc-state.md'
            state.parent.mkdir(parents=True)
            state.write_text('In progress\n', encoding='utf-8')
            assert project_reminder(Path(directory)) is not None
        print('OK: read-only reminder smoke test')
        return
    payload, warn = {}, ''
    try:
        raw = sys.stdin.buffer.read().decode('utf-8-sig', errors='replace').strip()
        if raw:
            payload = json.loads(raw)
    except (ValueError, OSError):
        warn = 'AI-DLC reminder: hook input could not be parsed (using the current directory); verify the hook configuration. '
    cwd = payload.get('cwd') if isinstance(payload, dict) else None
    root = Path(cwd) if isinstance(cwd, str) and cwd else Path.cwd()
    message = project_reminder(root)
    if message:
        print(warn + message)
    elif warn:
        print(warn.strip())

def project_reminder(root):
    # Require AI-DLC project state: do not print reminders for unrelated projects.
    try:
        root = root.resolve()
        state = root / 'aidlc-docs' / 'aidlc-state.md'
        if not state.is_file():
            return None
        handover = root / 'aidlc-docs' / 'collaboration' / 'HANDOVER.md'
        status = 'present; verify freshness' if handover.is_file() else 'missing; initialize from verified facts when appropriate'
        gov = ''
        text = state.read_text(encoding='utf-8', errors='replace')
        if '## Change Governance' in text:
            def field(name):
                line = next((l for l in text.splitlines() if name in l), '')
                return line.split(':', 1)[-1].strip() if ':' in line else 'unknown'
            gov = ('Change Governance: ticket=' + field('Jira Ticket') + '; evidence=' + field('Evidence Status') +
                   '; gates=' + field('Gates') + '. Restate these and re-read common/release-governance.md before editing code. ')
        return (gov + 'AI-DLC continuity: read aidlc-docs/aidlc-state.md first; '
                f'collaboration/HANDOVER.md is {status}. Reconcile active plans/task, approvals, '
                'actual Git diff and test evidence before resuming; checkpoint proactively. '
                'Hooks cannot save unfinished work.')
    except (OSError, RuntimeError):
        return None

if __name__ == '__main__':
    main()
