---
name: dialogue-lab-closeout
description: Close an Israel Facebook Dialogue Lab case after explicit user instruction, reported abandonment, no-response closure, or a clearly ended exchange. Use to validate closure, classify only observable outcomes, score the highest outcome, and record one controlled next test.
---

# Dialogue Lab Closeout

## Required inputs

- Target Case ID and the allowed closure condition.
- Any final public turn, reaction, or user report needed to establish the observable ending.

## Workflow

1. Read the complete live Manual, verify compatibility, record its revision, and validate the live Case Log schema.
2. Load the complete Case and Turn graph. Run `dialogue-lab validate-parent-graph`; resolve any required missing public turn before closure.
3. Verify privacy. Record observable chronology only. Never infer persuasion from silence, deletion, blocking, a reaction, or disappearance.
4. Choose the Manual-allowed closed status, Outcome Class, and highest outcome score reached. Record concise Outcome Notes, What Worked, What Failed, and exactly one Next Test.
5. Run `dialogue-lab validate-case` and `dialogue-lab validate-transition` on the planned result.
6. Re-read relevant rows, Pending Sync, source revision state, and schema. Run source-consistency before the explicit-approval write.
7. Read every written field back with `dialogue-lab verify-readback`. On failure, show PENDING SYNC and do not claim closure was recorded.

## Safety

- Do not close a case solely because no new message is visible unless the user requests or reports no-response closure.
- Do not alter canonical documents other than approved Case Log fields. Never post to Facebook.

## Output

Return a compact closeout receipt containing Case ID, final status, Outcome Score, Outcome Class, observable basis, What Worked, What Failed, Next Test, Manual revision, source-consistency result, and read-back result.
