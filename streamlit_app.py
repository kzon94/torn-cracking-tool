import os
from collections import Counter

import streamlit as st

# CONFIG

PASSWORD_FILE = "ignis-1M.txt"
TOP_N = 10
TOP_LETTERS_PER_POSITION = 3

st.set_page_config(
    page_title="Kzon's Torn Cracking Tool",
    layout="centered",
)


# CORE LOGIC

@st.cache_data(show_spinner=False)
def load_passwords(path: str) -> list[str]:
    """# Load dictionary and deduplicate"""
    passwords = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pw = line.strip()
            if pw:
                passwords.append(pw)
    return list(dict.fromkeys(passwords))


def filter_by_length(passwords: list[str], length: int) -> list[str]:
    """# Filter words by selected length"""
    return [pw for pw in passwords if len(pw) == length]


def apply_constraints(base_candidates, must_positions, forbid_positions):
    """# Apply known and forbidden letters to reduce candidate list"""
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
    """# Compute normalized score distribution"""
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
        raw_score = sum(char_prob.get(c, 0.0) for c in unique_chars)
        raw_scores.append((pw, raw_score))

    total_raw = sum(v for _, v in raw_scores)
    if total_raw <= 0:
        equal = 1.0 / len(candidates)
        return [(pw, equal) for pw, _ in raw_scores]

    scored = [(pw, v / total_raw) for pw, v in raw_scores]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def compute_position_frequencies(candidates: list[str]):
    """# Compute per-position character frequencies"""
    if not candidates:
        return []

    length = len(candidates[0])
    pos_freqs = [Counter() for _ in range(length)]
    for pw in candidates:
        for i, ch in enumerate(pw):
            pos_freqs[i][ch] += 1
    return pos_freqs


def format_forbid_map(forbid_positions):
    """# Format forbidden letters display"""
    parts = []
    for s in forbid_positions:
        if not s:
            parts.append(".")
        else:
            parts.append("{" + "".join(sorted(s)) + "}")
    return "".join(parts)


# LOAD DICTIONARY

base_path = os.path.dirname(os.path.abspath(__file__))
pw_path = os.path.join(base_path, PASSWORD_FILE)

if not os.path.exists(pw_path):
    st.error(f"Password file not found: `{pw_path}`")
    st.stop()

all_passwords = load_passwords(pw_path)


# UI

st.title("Kzon's Torn Cracking Tool")

with st.expander("How this app works", expanded=False):
    st.markdown(
        """
        1. Choose the **password length** and start a search.  
        2. Use **Known positions** to set letters you are sure about.  
        3. Use **Forbidden positions** to block letters in specific slots.  
        4. The tool shows the **best candidate passwords** and **letter frequencies**.

        Pattern rules:
        - `.` → unknown  
        - letter → required in this position (Known pattern)  
        - letter → forbidden in this position (Forbidden pattern)

        Examples (length 5):
        - Known: `..u..`  
        - Forbidden: `....o`
        """
    )

st.markdown("### Search settings")

length = st.number_input(
    "Password length",
    min_value=1,
    max_value=50,
    value=5,
    step=1,
)

start_search = st.button("Start / reset search", type="primary")


# SESSION STATE

if "current_length" not in st.session_state:
    st.session_state.current_length = None
    st.session_state.base_candidates = None
    st.session_state.current_candidates = None
    st.session_state.must_positions = None
    st.session_state.forbid_positions = None


if start_search:
    base_candidates = filter_by_length(all_passwords, length)
    if not base_candidates:
        st.warning(f"No passwords found with length {length}.")
    else:
        st.session_state.current_length = length
        st.session_state.base_candidates = base_candidates
        st.session_state.must_positions = [None] * length
        st.session_state.forbid_positions = [set() for _ in range(length)]
        st.session_state.current_candidates = base_candidates[:]


if st.session_state.current_candidates is None:
    st.stop()

current_length = st.session_state.current_length
must_positions = st.session_state.must_positions
forbid_positions = st.session_state.forbid_positions
current_candidates = st.session_state.current_candidates


# CONSTRAINTS UI

st.markdown("### Constraints")

must_str = "".join(c if c is not None else "." for c in must_positions)
forbid_str = format_forbid_map(forbid_positions)

st.markdown(f"**Known pattern:** `{must_str}`")
st.markdown(f"**Forbidden map:** `{forbid_str}`")

col_a, col_d = st.columns(2)

with col_a:
    pattern_a = st.text_input(
        "Known positions",
        placeholder="Example: ..u..",
        max_chars=current_length,
    )
    apply_a = st.button("Apply known pattern")

with col_d:
    pattern_d = st.text_input(
        "Forbidden positions",
        placeholder="Example: ....o",
        max_chars=current_length,
    )
    apply_d = st.button("Apply forbidden pattern")


# Known pattern
if apply_a:
    if len(pattern_a) != current_length:
        st.error(f"Pattern length must be {current_length}.")
    else:
        for i, ch in enumerate(pattern_a):
            if ch == ".":
                continue
            if must_positions[i] is not None and must_positions[i] != ch:
                st.warning(
                    f"Conflict at position {i+1}. Keeping existing letter."
                )
                continue
            must_positions[i] = ch

        st.session_state.current_candidates = apply_constraints(
            st.session_state.base_candidates,
            must_positions,
            forbid_positions,
        )
        current_candidates = st.session_state.current_candidates


# Forbidden pattern
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


# CANDIDATES DISPLAY

st.markdown("---")
st.markdown("### Candidates & probabilities")

if not current_candidates:
    st.error("No possible passwords remain.")
    st.stop()

scored = score_candidates(current_candidates)
limit = min(TOP_N, len(scored))

st.write(f"Total candidates: **{len(current_candidates)}**")
st.write(f"Showing top **{limit}** options:")

rows = [
    {"Password": pw, "Score (%)": f"{score * 100:.5f}"}
    for pw, score in scored[:limit]
]
st.table(rows)


# POSITION FREQUENCIES

st.markdown("### Letter frequencies by position")

pos_freqs = compute_position_frequencies(current_candidates)
total = len(current_candidates)

lines = []
any_printed = False

for idx in range(current_length):
    if must_positions[idx] is not None:
        continue

    freq = pos_freqs[idx]
    if not freq:
        continue

    any_printed = True
    sorted_letters = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top = sorted_letters[:TOP_LETTERS_PER_POSITION]

    parts = [
        f"`{ch}` ({count / total * 100:.1f}%)"
        for ch, count in top
    ]
    lines.append(f"- **Pos {idx+1}**: " + ", ".join(parts))

if not any_printed:
    st.info("All positions are already fixed.")
else:
    st.markdown("\n".join(lines))

