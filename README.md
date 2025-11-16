# Kzon’s Torn Cracking Tool

*Kzon’s Torn Cracking Tool* is a Streamlit-based analytical assistant designed to narrow down password candidates in the game **Torn**.
The tool evaluates large password dictionaries and progressively filters them using known and forbidden character positions.
A normalized statistical model is then applied to identify the most probable remaining candidates.

This application does **not** perform brute-force attacks.
Its purpose is analytical: given partial information from Torn’s mini-game, it ranks all dictionary candidates by likelihood.

---

## Overview

The Streamlit application provides:

* Selection of password length
* Application of known character positions
* Application of forbidden characters by position
* Real-time filtering of candidate passwords
* Normalized probability scoring
* Per-position letter frequency analysis
* Support for dictionaries with over one million entries
* Persistent state during interaction

---

## Requirements

* Python 3.9 or newer
* Required package:

```
pip install streamlit
```

---

## File Structure

```
torn-cracking-tool/
│
├── streamlit_app.py        # Streamlit interface
├── ignis-1M.txt            # Password dictionary
└── README.md               # Documentation
```

---

## Usage

Start the application with:

```
streamlit run streamlit_app.py
```

### User Workflow

1. Select the **password length**.
2. Click **Start / reset search**.
3. Enter a **known-positions pattern**, using `.` for unknown characters:

   ```
   ..u..
   ```
4. Enter a **forbidden-positions pattern** to exclude letters from specific positions:

   ```
   ....o
   ```
5. The interface will display:

   * A ranked list of candidate passwords with normalized probability scores
   * Letter frequency distributions for unresolved positions

Updates occur immediately after each new constraint.

---

## Scoring Method

The tool evaluates remaining candidates using a normalized probability model:

1. All characters across remaining candidates are counted.
2. Each character is assigned a probability:
   `P(c) = frequency(c) / total_characters`.
3. Each candidate password receives a raw score equal to the sum of probabilities of its unique characters.
4. Raw scores are normalized so that their total equals 1.

Higher scores indicate higher relative likelihood given the constraints.

---

## Dictionary Source Acknowledgement

This project uses the **ignis-1M.txt** password dictionary provided by **ignis-sec**:

**[https://github.com/ignis-sec/Pwdb-Public/blob/master/wordlists/ignis-1M.txt](https://github.com/ignis-sec/Pwdb-Public/blob/master/wordlists/ignis-1M.txt)**

Thx ignis-sec for making this resource publicly available.

---

## License

This project is provided under the **MIT License**.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
