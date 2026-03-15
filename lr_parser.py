# Hasan Demir b231202054
# Ahmet Yiğit b231202049

import sys
import os

# ─────────────────────────────────────────────
# 1. PARSE TABLE & GRAMMAR LOADING FROM FILES
# ─────────────────────────────────────────────

def load_action_table(path):
    """
    Reads ActionTable.txt and builds action_table dict.
    Column order: id  +  *  (  )  $
    """
    col_map = {0: 'id', 1: '+', 2: '*', 3: '(', 4: ')', 5: '$'}
    table = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('State')]
    for line in lines:
        parts = line.split()
        state = int(parts[0])
        table[state] = {}
        for col_idx, val in enumerate(parts[1:]):
            if val != '-':
                table[state][col_map[col_idx]] = val
    return table


def load_goto_table(path):
    """
    Reads GotoTable.txt and builds goto_table dict.
    Column order: E  T  F
    """
    col_map = {0: 'E', 1: 'T', 2: 'F'}
    table = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('State')]
    for line in lines:
        parts = line.split()
        state = int(parts[0])
        row = {}
        for col_idx, val in enumerate(parts[1:]):
            if val != '-':
                row[col_map[col_idx]] = int(val)
        if row:
            table[state] = row
    return table


def load_grammar(path):
    """
    Reads Grammar.txt and builds grammar dict:
      rule_num -> (lhs_symbol, rhs_length)
    Expected format:  1 E -> E + T
    """
    grammar = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # "1 E -> E + T"
            parts = line.split()
            rule_num = int(parts[0])
            lhs = parts[1]          # E / T / F
            rhs = parts[3:]         # tokens after '->'
            grammar[rule_num] = (lhs, len(rhs))
    return grammar


# ─────────────────────────────────────────
# 2. PARSE TREE NODE
# ─────────────────────────────────────────

class Node:
    def __init__(self, value):
        self.value = value
        self.children = []


def print_parse_tree(node, path="", out=None):
    """DFS traversal; prints /E/T/F style paths."""
    current = path + "/" + node.value
    print(current, file=out)
    for child in node.children:
        print_parse_tree(child, current, out)


# ─────────────────────────────────────────
# 3. TOKEN READER
# ─────────────────────────────────────────

def read_tokens(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip().split()
    except FileNotFoundError:
        return None


# ─────────────────────────────────────────
# 4. LR PARSER
# ─────────────────────────────────────────

VALID_TOKENS = {'id', '+', '*', '(', ')', '$'}
SEP = "-" * 104


def parse(tokens, action_table, goto_table, grammar, out=None):
    """
    Canonical LR(1) parser.

    Output format matches the reference test cases exactly:
      - Each row is printed BEFORE the action is applied (correct snapshot).
      - Stack column shows the current stack string.
      - Input column shows the remaining input INCLUDING the current token.
      - Action column shows what will be done.
      - The accept row is also printed in the table.
    """

    stack = [0]
    buf = tokens[:]         # mutable copy
    tree_stack = []

    def stack_str():
        return "".join(str(x) for x in stack)

    def input_str():
        return " ".join(buf)

    print(f"{'Stack':<40} {'Input':<40} {'Action'}", file=out)
    print(SEP, file=out)

    while True:
        state = stack[-1]
        token = buf[0]

        # ── Unknown token check ──────────────────────────────────────
        if token not in VALID_TOKENS:
            print(f"Unknown token: {token}", file=out)
            return False

        # ── Look up action ───────────────────────────────────────────
        action = action_table.get(state, {}).get(token)

        if action is None:
            # Syntax error
            print(SEP, file=out)
            print(f"SYNTAX ERROR at token: {token}", file=out)
            print("Parse tree:", file=out)
            if tree_stack:
                print_parse_tree(tree_stack[-1], out=out)
            return False

        # ── Build action label (computed here so we can use pre-action state) ──
        if action == 'accept':
            action_label = "accept"
        elif action.startswith('s'):
            action_label = f"Shift {action[1:]}"
        else:                               # reduce
            rule_num_label = int(action[1:])
            lhs_label, rhs_len_label = grammar[rule_num_label]
            # The state exposed after popping is what goes into GOTO[state, lhs]
            # We can compute it without modifying the stack:
            exposed_state = stack[-(2 * rhs_len_label + 1)]
            goto_state_label = goto_table[exposed_state][lhs_label]
            action_label = f"Reduce {rule_num_label} (GOTO [{exposed_state}, {lhs_label}])"

        # ── Print the current snapshot BEFORE applying the action ────

        print(f"{stack_str():<40} {input_str():<40} {action_label}", file=out)

        # ── Apply action ─────────────────────────────────────────────
        if action == 'accept':
            print(SEP, file=out)
            print("Parse tree:", file=out)
            print_parse_tree(tree_stack[0], out=out)
            return True

        elif action.startswith('s'):
            next_state = int(action[1:])
            stack.append(token)
            stack.append(next_state)
            tree_stack.append(Node(token))
            buf.pop(0)

        else:                               # reduce
            rule_num = int(action[1:])
            lhs, rhs_len = grammar[rule_num]

            # pop 2*rhs_len items (symbol + state for each RHS token)
            for _ in range(2 * rhs_len):
                stack.pop()

            top_state = stack[-1]
            goto_state = goto_table[top_state][lhs]
            stack.append(lhs)
            stack.append(goto_state)

            # Build parse tree node
            children = [tree_stack.pop() for _ in range(rhs_len)]
            children.reverse()
            parent = Node(lhs)
            parent.children = children
            tree_stack.append(parent)


# ─────────────────────────────────────────
# 5. MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    # ── Load tables once ────────────────────────────────────────────
    ACTION_TABLE_FILE = os.path.join("Files", "ActionTable.txt")
    GOTO_TABLE_FILE   = os.path.join("Files", "GotoTable.txt")
    GRAMMAR_FILE      = os.path.join("Files", "Grammar.txt")

    # Graceful fallback: if Files/ directory is absent, use hardcoded tables
    # (keeps the code runnable even without the data files)
    try:
        action_table = load_action_table(ACTION_TABLE_FILE)
        goto_table   = load_goto_table(GOTO_TABLE_FILE)
        grammar      = load_grammar(GRAMMAR_FILE)
        print("Tables loaded from files.\n")
    except FileNotFoundError as e:
        print(f"Warning: could not load data files ({e}). Using built-in tables.\n")
        grammar = {1:('E',3), 2:('E',1), 3:('T',3), 4:('T',1), 5:('F',3), 6:('F',1)}
        action_table = {
            0: {'id':'s5', '(':'s4'},
            1: {'+':'s6', '$':'accept'},
            2: {'+':'r2', '*':'s7', ')':'r2', '$':'r2'},
            3: {'+':'r4', '*':'r4', ')':'r4', '$':'r4'},
            4: {'id':'s5', '(':'s4'},
            5: {'+':'r6', '*':'r6', ')':'r6', '$':'r6'},
            6: {'id':'s5', '(':'s4'},
            7: {'id':'s5', '(':'s4'},
            8: {'+':'s6', ')':'s11'},
            9: {'+':'r1', '*':'s7', ')':'r1', '$':'r1'},
            10:{'+':'r3', '*':'r3', ')':'r3', '$':'r3'},
            11:{'+':'r5', '*':'r5', ')':'r5', '$':'r5'},
        }
        goto_table = {
            0:{'E':1,'T':2,'F':3},
            4:{'E':8,'T':2,'F':3},
            6:{'T':9,'F':3},
            7:{'F':10},
        }

    # ── Process all input files ──────────────────────────────────────
    print("LR Parser running...\n")

    for i in range(1, 10):
        input_file  = f"input{i}.txt"
        output_file = f"output{i}.txt"

        tokens = read_tokens(input_file)
        if tokens is None:
            print(f"Warning: {input_file} not found, skipping.")
            continue

        print(f"Processing: {input_file} -> {output_file}")

        original_stdout = sys.stdout
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                parse(tokens, action_table, goto_table, grammar, out=f)
        finally:
            sys.stdout = original_stdout

    print("\nAll output files generated successfully.")