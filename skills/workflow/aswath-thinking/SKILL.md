---
name: aswath-thinking
description: Use when approaching non-trivial architecture problems, ungrounded prompts, or complex decision trade-offs before any code is written
---

## Overview

Deconstruct ungrounded assumptions via first principles, inversion, and adversarial verification before executing code.

AI coding assistants often accept vague, high-level requests and immediately fabricate implementation code based on silent, ungrounded assumptions, leading to massive rewrites. `aswath-thinking` enforces a strict 4-stage cognitive reasoning pipeline before modifying any files.

## The 4-Stage Reasoning Pipeline

1. **Assumptions Check**
   - Identify and list every unproven, implicit assumption made in the prompt or requirements.
   - Example: Does the caller expect streaming or batched results? Is in-memory storage sufficient, or is persistence required across restarts?

2. **Inversion Analysis (Failure Mode Forensics)**
   - Invert the problem: How could this design fail catastrophically in production?
   - Analyze failure modes: upstream 429 rate limits, network partitions, state drift, memory leaks, and race conditions.

3. **MECE Decision Tree**
   - Structure choices into mutually exclusive, collectively exhaustive (MECE) branches.
   - Surface trade-offs explicitly (e.g., local LRU cache vs disk-backed store) and lock architectural decisions before implementation.

4. **Verification Gate**
   - Define concrete, falsifiable acceptance criteria.
   - Proceed to specification or execution only when 100% of ambiguities are surfaced and aligned.
