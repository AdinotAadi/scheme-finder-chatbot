#!/usr/bin/env python3
"""Claude PreToolUse hook: block application-code edits until a Jira ticket key is recorded.

Reads hook JSON on stdin. Exit 2 (with a message on stderr) blocks the tool call.
Read-only: never writes files. Fails open on any parsing/IO error so it cannot wedge a session.
Policy source: common/release-governance.md Gate G0.
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

EDIT_TOOLS = {'Edit', 'Write', 'NotebookEdit', 'MultiEdit'}
COMMIT_RE = re.compile(r'\bgit\s+(?:-C\s+(?:"[^"]*"|'+"'[^']*'"+r'|\S+)\s+)?commit\b')
MSG_RE = re.compile(r'(?:\s-[a-zA-Z]*m\b|\s--message\b)')
KEY_RE = re.compile(r'\b[A-Z][A-Z0-9]+-\d+\b')


def find_state(path):
    for parent in [path.parent, *path.parent.parents]:
        state = parent / 'aidlc-docs' / 'aidlc-state.md'
        if state.is_file():
            return parent, state
    return None, None


def check(file_path):
    """Return a block message, or None to allow."""
    path = Path(file_path).resolve()
    root, state = find_state(path)
    if state is None:
        # Opt-in strict mode (AIDLC_STRICT=1): inside a git repo with no AI-DLC state, source edits are blocked
        # until the workflow creates aidlc-docs/aidlc-state.md. Off by default so unrelated repos are unaffected.
        if os.environ.get('AIDLC_STRICT') == '1' and any((p / '.git').exists() for p in [path.parent, *path.parent.parents]):
            return ('AI-DLC governance (strict mode): no aidlc-docs/aidlc-state.md in this repository. Create it '
                    '(Gate G0 in common/release-governance.md) before editing application code.')
        return None  # not an AI-DLC project
    try:
        path.relative_to(root / 'aidlc-docs')
        return None  # documentation is always editable
    except ValueError:
        pass
    text = state.read_text(encoding='utf-8', errors='replace')
    if '## Change Governance' not in text:
        return ('AI-DLC governance: aidlc-state.md has no "## Change Governance" section. '
                'Record the Jira ticket (Gate G0, common/release-governance.md) before editing application code.')
    lowered = text.lower()
    ticket = next((l for l in text.splitlines() if 'jira ticket' in l.lower()), '')
    # The field VALUE must start with a key (a key buried in "MISSING (waiting for ABC-1)" does not count).
    has_key = re.search(r':\s*\**\s*[A-Z][A-Z0-9]+-\d+', ticket) is not None
    if not has_key:
        # Permitted no-ticket deviation: G0 explicitly set to Deviation, not customer-facing, no escalation.
        g0_deviation = re.search(r'g0\W{0,3}deviation', lowered) is not None
        not_customer = re.search(r'customer-facing\W{0,4}no\b', lowered) is not None
        escalation = any('escalation' in l for l in lowered.splitlines() if 'origin' in l or 'change type' in l)
        if not (g0_deviation and not_customer and not escalation):
            return ('AI-DLC governance: no Jira ticket key recorded (Gate G0). Application-code edits are blocked '
                    'until a key is recorded in aidlc-state.md under "## Change Governance". '
                    'Customer-facing or escalation work has no no-ticket deviation path.')
    # Gate G1: evidence status must be Verified / Not applicable / explicit exception before code edits.
    # A missing Evidence Status line counts as G1 open: the state template always includes it.
    evidence = next((l for l in text.splitlines() if 'evidence status' in l.lower()), None)
    if evidence is None:
        return ('AI-DLC governance: no "Evidence Status (G1)" line in aidlc-state.md under "## Change Governance". '
                'Record Verified / Not applicable (non-fix change) / Exception before editing application code.')
    value = evidence.split(':', 1)[-1].lower()
    excepted = 'exception' in value and '/' not in value
    ok = excepted or (('verified' in value or 'not applicable' in value) and 'hypothesis' not in value and '/' not in value)
    if not ok:
        return ('AI-DLC governance: Gate G1 is open (Evidence Status is not Verified / Not applicable / '
                'exception logged). Application-code edits are blocked until root-cause evidence is recorded '
                'or the user records an explicit exception in audit.md.')
    return None


CD_RE = re.compile(r'(?:\bcd\s+(?:/d\s+)?|\bgit\s+-C\s+|-LiteralPath\s+|Set-Location\s+)["\']?([^"\'&;|\r\n]+?)["\']?\s*(?:&&|;|\||$|\s-|\s+commit\b)')


def command_dirs(command, cwd):
    """Directories a shell command may run in: any `cd X` / `git -C X` target first, then the hook cwd."""
    dirs = []
    for match in CD_RE.finditer(command + ' ;'):
        raw = match.group(1).strip()
        if len(raw) > 2 and raw[0] == '/' and raw[2] == '/':  # msys path /c/Users/... -> C:/Users/...
            raw = raw[1].upper() + ':' + raw[2:]
        p = Path(raw)
        if not p.is_absolute():
            p = Path(cwd or '.') / p
        dirs.append(p.resolve())
    dirs.append(Path(cwd or '.').resolve())
    return dirs


def check_commit(command, cwd):
    """Block `git commit -m ...` without a ticket key (works even when core.hooksPath bypasses repo hooks)."""
    if not COMMIT_RE.search(command) or not MSG_RE.search(command):
        return None  # not a commit, or message comes from an editor/file (cannot inspect)
    if KEY_RE.search(command):
        return None
    root, state = None, None
    for base in command_dirs(command, cwd):
        root, state = find_state(base / 'x')
        if state is not None:
            break
    if state is None:
        return None
    try:
        import subprocess
        branch = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--abbrev-ref', 'HEAD'],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        branch = ''
    if branch.startswith('wip/NO-TICKET-'):
        return None
    return ('AI-DLC governance: commit message must reference a Jira ticket key, e.g. '
            '"fix(scope): summary [PROJ-1234]" (Gate G2).')


def main():
    if '--self-test' in sys.argv:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'aidlc-docs').mkdir()
            src = root / 'app.py'
            state = root / 'aidlc-docs' / 'aidlc-state.md'
            state.write_text('## Change Governance\n- **Jira Ticket(s)**: MISSING\n', encoding='utf-8')
            assert check(str(src)) is not None
            assert check(str(root / 'aidlc-docs' / 'x.md')) is None
            os.environ['AIDLC_STRICT'] = '1'
            with tempfile.TemporaryDirectory() as d2:
                bare = Path(d2)
                (bare / '.git').mkdir()
                assert check(str(bare / 'app.py')) is not None  # strict: git repo without state
                os.environ['AIDLC_STRICT'] = '0'
                assert check(str(bare / 'app.py')) is None  # default: fail open
            os.environ.pop('AIDLC_STRICT', None)
            state.write_text('## Change Governance\n- **Jira Ticket(s)**: IDV-1\n', encoding='utf-8')
            assert check(str(src)) is not None  # key but no Evidence Status line: G1 open
            state.write_text('## Change Governance\n- **Jira Ticket(s)**: IDV-1\n- **Evidence status**: Verified\n', encoding='utf-8')
            assert check(str(src)) is None  # lower-case field name accepted
            state.write_text('## Change Governance\n- **jira ticket(s)**: IDV-1\n- **Evidence Status (G1)**: Hypothesis-only\n', encoding='utf-8')
            assert check(str(src)) is not None
            state.write_text('## Change Governance\n- **Jira Ticket(s)**: MISSING\n- **Customer-Facing**: Yes\n- **Gates**: G0 Deviation\n', encoding='utf-8')
            assert check(str(src)) is not None
            assert check_commit('git commit -m "feat: x"', str(root)) is not None
            assert check_commit('git commit -m "feat: x [ABC-1]"', str(root)) is None
            assert check_commit('git status', str(root)) is None
            # the commit may target a project other than the hook cwd (cd X && git commit / git -C X commit)
            other = str(Path.cwd())
            assert check_commit('cd "%s" && git add -A && git commit -m "x"' % root.as_posix(), other) is not None
            assert check_commit('git -C "%s" commit -m "x"' % root.as_posix(), other) is not None
            assert check_commit('cd "%s" && git commit -m "x [ABC-1]"' % root.as_posix(), other) is None
        print('OK: governance guard self-test')
        return
    try:
        payload = json.load(sys.stdin)
        inp = payload.get('tool_input') or {}
        if payload.get('tool_name') in ('Bash', 'PowerShell'):
            message = check_commit(str(inp.get('command') or ''), payload.get('cwd'))
            if message:
                print(message, file=sys.stderr)
                sys.exit(2)
            return
        if payload.get('tool_name') not in EDIT_TOOLS:
            return
        target = inp.get('file_path') or inp.get('notebook_path')
        if not target:
            return
        message = check(target)
    except Exception:
        return  # fail open
    if message:
        print(message, file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
