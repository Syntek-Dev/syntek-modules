# Coding Principles

**Last Updated**: 17/02/2026
**Version**: 1.4.0
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Rob Pike's 5 Rules of Programming](#rob-pikes-5-rules-of-programming)
- [Linus Torvalds' Coding Rules](#linus-torvalds-coding-rules)
- [Summary](#summary)

---

## Overview

These principles guide all code written in this project. They are derived from
two of the most influential systems programmers — Rob Pike (co-creator of Go)
and Linus Torvalds (creator of Linux). Together they emphasise simplicity,
data-driven design, and avoiding premature optimisation.

---

## Rob Pike's 5 Rules of Programming

> Originally from "Notes on Programming in C" (1989), cited widely in the Go community.

**Rule 1 — Don't guess bottlenecks**
You cannot tell where a programme will spend its time. Bottlenecks occur in
surprising places. Do not second-guess and add speed hacks until you know
where the bottleneck actually is.

**Rule 2 — Measure before tuning**
Do not tune for speed until you have measured. Even then, do not tune unless one part of the code overwhelms the rest.

**Rule 3 — Fancy algorithms are slow when N is small**
Fancy algorithms are slow when N is small, and N is usually small. Fancy
algorithms have big constants. Until you know that N is frequently large, don't
get fancy. Even if N does get large, apply Rule 2 first.

**Rule 4 — Fancy algorithms are buggy**
Fancy algorithms are more complex and much harder to implement correctly. Use
simple, reusable, and easy-to-maintain algorithms. Use simple data structures
too.

**Rule 5 — Data structures dominate**
Data dominates. If you have chosen the right data structures and organised
things well, the algorithms will almost always be self-evident. Data structures
are central to programming — not algorithms.

---

## Linus Torvalds' Coding Rules

> Derived from Linus Torvalds' coding style documents, talks, and mailing list contributions.

### Rule 1 — Data structures over algorithms

_"Show me your flowcharts and conceal your tables, and I shall continue to be
mystified. Show me your tables, and I won't usually need your flowcharts;
they'll be obvious."_

Focus on how data is organised. A solid data model often eliminates the need
for complex, messy code. The logic naturally follows from the structure.

### Rule 2 — Good taste in coding

- Remove special cases: good code eliminates edge cases rather than adding
  `if` statements for them
- Simplify logic: avoid tricky expressions or complex, deeply nested control
  flows
- Reduce branches: fewer conditional statements make code faster (CPU branch
  prediction) and easier to reason about

### Rule 3 — Readability and maintainability

- Short functions: functions do one thing, are short, and fit on one or two
  screenfuls of text
- Descriptive names: variables and functions should be descriptive but concise
- Avoid excessive indentation: deep nesting makes code hard to read, especially
  after staring at it for hours

### Rule 4 — Code structure and style

- Avoid multiple assignments on a single line
- One operation per statement — clarity beats cleverness

### Rule 5 — Favour stability over complexity

Do not do something clever just because you can. Stability and predictability
are more valuable than clever or novel approaches.

### Rule 6 — Make it work, then make it better

Get it working first, then optimise. Do not over-optimise during initial
implementation. All code should be maintainable by anyone, not just the
original author.

---

## Summary

| Principle                 | Core Idea                                |
| ------------------------- | ---------------------------------------- |
| Don't optimise early      | Measure first, then act                  |
| Keep algorithms simple    | Fancy = slow, buggy, unmaintainable      |
| Data structures first     | Good data models make algorithms obvious |
| Eliminate special cases   | Design away edge cases, don't patch them |
| Short, focused functions  | One thing, readable, maintainable        |
| Stability over cleverness | Boring, predictable code is good code    |
| Make it work first        | Ship, measure, then improve              |
