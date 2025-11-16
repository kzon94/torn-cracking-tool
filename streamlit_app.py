import os
from collections import Counter

import streamlit as st

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

PASSWORD_FILE = "ignis-1M.txt"
TOP_N = 20
TOP_LETTERS_PER_POSITION = 3

st.set_page_config(
    page_title="Kzon's Torn Cracking Tool",
    layout="centered",
)


# -----------------------------------------------------------------------------
# CORE LOGIC (misma idea que en bruteforce-helper)
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_passwords(path: str) -> list[str]:
    passwords = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pw = line.strip()
            if pw:
                passwords.append(pw)
    # deduplicate preserving order
    return list(dict.fromkeys(passwords))


def filter_by_length(passwords: list[str], length: int) -> list[str]:
    return [pw for pw in passwords if len(pw) == length]


def apply_constraints(base_candidates, must_positions, forbid_positions):
    filtered = []
    for pw in base_candidates:
        ok = True
        for i, ch in enumerate(pw):
            must = must_positions[i]
            if must is not None and ch != must:
                ok = False
                break
            if forbid_positions[i] and ch in forbid_positions[i]:
                ok = False
                break
        if ok:
            filtered.append(pw)
    return filtered


def score_candidates(candidates: list[str]) -> list[tuple[str, float]]:
    """Distribución normalizada de scores."""
    if not candidates:
        return []

    all_chars = "".join(candidates)
    char_freq = Counter(all_chars)
    total_chars = sum(char_freq.values())
    if total_chars == 0:
        equal = 1.0 / len(candidates)
        return [(pw, equal) for pw in candidates]

    char_prob = {ch: cnt / total_chars for ch, cnt in char_freq.items()}

    raw_scores = []
    for pw in candidates:
        unique_chars = set(pw)
        raw = sum(char_prob.get(c, 0.0) for c in unique_chars)
        raw_scores.append((pw, raw))

    total_raw = sum(v for _, v in raw_scores)
    if total_raw <= 0:
        equal = 1.0 / len(candidates)
        return [(pw, equal) for pw, _ in raw_scores]

    scored = [(pw, v / total_raw) for pw, v in raw_scores]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def compute_position_frequencies(candidates: list[str]):
    if not candidates:
        return []
    length = len(candidates[0])
    pos_freqs = [Counter() for _ in range(length)]
    for pw in candidates:
        for i, ch in enumerate(pw):
            pos_freqs[i][ch] += 1
    return pos_freqs


def format_forbid_map(forbid_positions):
    parts = []
    for s in forbid_positions:
        if not s:
            parts.append(".")
        else:
            parts.append("{" + "".join(sorted(s)) + "}")
    return "".join(parts)


# -----------------------------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
pw_path = os.path.join(base_path, PASSWORD_FILE)

if not os.path.exists(pw_path):
    st.error(f"Password file not found: `{pw_path}`")
    st.stop()

all_passwords = load_passwords(pw_path)


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------

st.title("Kzon's Torn Cracking Tool")

with st.expander("How this app works", expanded=False):
    st.markdown(
        """
        1. Choose the **password length** and start a search.  
        2. Use **Known positions** (`-a` style pattern) to set letters you are sure about.  
        3. Use **Forbidden positions** (`-d` style pattern) to block letters in specific slots.  
        4. The app will show the **best candidate passwords** and **letter frequencies** for the remaining positions.
        
        Pattern rules:
        - `.` → unknown position  
        - Any letter → fixed at that position (for Known pattern)  
        - Any letter → forbidden at that position (for Forbidden pattern)  
        
        Examples (length 5):
        - Known: `..u..` → position 3 must be `u`  
        - Forbidden: `....o` → position 5 cannot be `o`
        """
    )

st.markdown("### Search settings")

col_len, col_btn = st.columns([1, 1])

with col_len:
    length = st.number_input(
        "Password length",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
    )

with col_btn:
    start_search = st.button("Start / reset search", type="primary")

# Session state init
if "current_length" not in st.session_state:
    st.session_state.current_length = None
    st.session_state.base_candidates = None
    st.session_state.current_candidates = None
    st.session_state.must_positions = None
    st.session_state.forbid_positions = None

# Handle start/reset
if start_search:
    base_candidates = filter_by_length(all_passwords, length)
    if not base_candidates:
        st.warning(f"No passwords with length {length}.")
    else:
        st.session_state.current_length = length
        st.session_state.base_candidates = base_candidates
        st.session_state.must_positions = [None] * length
        st.session_state.forbid_positions = [set() for _ in range(length)]
        st.session_state.current_candidates = base_candidates[:]

# Only continue if we have an active search
if st.session_state.current_candidates is None:
    st.stop()

current_length = st.session_state.current_length
must_positions = st.session_state.must_positions
forbid_positions = st.session_state.forbid_positions
current_candidates = st.session_state.current_candidates

st.markdown("### Constraints")

must_str = "".join(c if c is not None else "." for c in must_positions)
forbid_str = format_forbid_map(forbid_positions)

st.markdown(f"**Current known pattern (-a):** `{must_str}`")
st.markdown(f"**Current forbidden map (-d):** `{forbid_str}`")

col_a, col_d = st.columns(2)

with col_a:
    pattern_a = st.text_input(
        "Known positions pattern (-a)",
        placeholder="Example: ..u..",
        max_chars=current_length,
    )
    apply_a = st.button("Apply known pattern (-a)")

with col_d:
    pattern_d = st.text_input(
        "Forbidden positions pattern (-d)",
        placeholder="Example: ....o",
        max_chars=current_length,
    )
    apply_d = st.button("Apply forbidden pattern (-d)")


# Apply -a pattern
if apply_a:
    if len(pattern_a) != current_length:
        st.error(f"Pattern length must be {current_length}.")
    else:
        for i, ch in enumerate(pattern_a):
            if ch == ".":
                continue
            if must_positions[i] is not None and must_positions[i] != ch:
                st.warning(
                    f"Conflict at position {i+1}: "
                    f"existing '{must_positions[i]}' vs new '{ch}'. Keeping existing."
                )
                continue
            must_positions[i] = ch

        st.session_state.current_candidates = apply_constraints(
            st.session_state.base_candidates,
            must_positions,
            forbid_positions,
        )
        current_candidates = st.session_state.current_candidates

# Apply -d pattern
if apply_d:
    if len(pattern_d) != current_length:
        st.error(f"Pattern length must be {current_length}.")
    else:
        for i, ch in enumerate(pattern_d):
            if ch == ".":
                continue
            forbid_positions[i].add(ch)

        st.session_state.current_candidates = apply_constraints(
            st.session_state.base_candidates,
            must_positions,
            forbid_positions,
        )
        current_candidates = st.session_state.current_candidates

st.markdown("---")
st.markdown("### Candidates & probabilities")

if not current_candidates:
    st.error("No possible passwords remain with these constraints.")
    st.stop()

scored = score_candidates(current_candidates)
limit = min(TOP_N, len(scored))

st.write(f"Current candidates: **{len(current_candidates)}**")
st.write(f"Showing top **{limit}** options:")

# Build table for display
table_rows = [
    {"Password": pw, "Score (prob. %)": f"{score * 100:.5f}"}
    for pw, score in scored[:limit]
]
st.table(table_rows)

st.markdown("### Letter frequencies by position")

pos_freqs = compute_position_frequencies(current_candidates)
total = len(current_candidates)

lines = []
any_printed = False
for idx in range(current_length):
    if must_positions[idx] is not None:
        continue  # skip fixed positions
    freq = pos_freqs[idx]
    if not freq:
        continue
    any_printed = True
    sorted_letters = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_letters = sorted_letters[:TOP_LETTERS_PER_POSITION]
    parts = [
        f"`{ch}` ({count / total * 100:.1f}%)"
        for ch, count in top_letters
    ]
    lines.append(f"- **Pos {idx+1}**: " + ", ".join(parts))

if not any_printed:
    st.info("All positions are already fixed.")
else:
    st.markdown("\n".join(lines))

