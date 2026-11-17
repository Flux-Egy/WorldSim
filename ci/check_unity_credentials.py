#!/usr/bin/env python3
"""Sanity-checks UNITY_EMAIL / UNITY_PASSWORD WITHOUT printing their values.

The repo is public, so CI logs are public: this prints only booleans (and the email's
length, which the owner can compare with what they expect). It exists because typing
secrets on a phone with a non-Latin keyboard can silently insert Arabic-Indic digits,
direction marks or zero-width characters, which Unity then rejects as
"Invalid Credential" (143.002). Exit code 1 means a definite format problem was found.
"""
import os
import sys

INVISIBLE = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D,
             0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF, 0x00A0}


def facts(value):
    return {
        "set": bool(value),
        "ascii_only": value.isascii(),
        "invisible_or_direction_chars": any(ord(c) in INVISIBLE for c in value),
        "non_latin_digits": any(c.isdigit() and not c.isascii() for c in value),
        "leading_or_trailing_whitespace": value != value.strip(),
        "contains_newline": "\n" in value or "\r" in value,
    }


def main():
    email = os.environ.get("UNITY_EMAIL", "")
    password = os.environ.get("UNITY_PASSWORD", "")

    e = facts(email)
    e.update({
        "length": len(email),
        "exactly_one_at_sign": email.count("@") == 1,
        "contains_space": " " in email,
        "has_uppercase": email != email.lower(),
    })
    p = facts(password)

    problems = []
    for name, f in (("UNITY_EMAIL", e), ("UNITY_PASSWORD", p)):
        print(f"{name}:")
        for k, v in f.items():
            print(f"  {k}: {v}")
        if not f["set"]:
            problems.append(f"{name} is empty")
        if f["invisible_or_direction_chars"]:
            problems.append(f"{name} contains invisible / text-direction characters")
        if f["non_latin_digits"]:
            problems.append(f"{name} contains non-Latin digits (e.g. Arabic-Indic)")
        if f["leading_or_trailing_whitespace"] or f["contains_newline"]:
            problems.append(f"{name} has extra whitespace or a newline")
    if email and not e["exactly_one_at_sign"]:
        problems.append("UNITY_EMAIL does not look like an email address")
    if not e["ascii_only"]:
        problems.append("UNITY_EMAIL contains non-ASCII characters")

    for msg in problems:
        print(f"::error::{msg}. Re-enter it (see GITHUB_ACTIONS.md, 'Troubleshooting licensing').")
    if not problems:
        print("No format problems found. If Unity still says 'Invalid Credential', the values "
              "themselves are wrong: test them by signing in at https://id.unity.com.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
