# funnel_probe — results (Mandala-Computing)

LABEL: DISCRETE ANALOG, OPEN-LOOP SLOW DRIVE. The annealer's cooling rate
stands in for eps and reads the step counter, never the state; the paper's
slow variable is state-coupled. Nothing in the root modules was edited.
`quantum_mandala.py` EXCLUDED as ordered.

Pre-registration: commit f0be578. Step 1 (noise): `NOISE_RESULTS.md`,
commit 35f4069. Code: `exhaustive_anneal.py`, commit 5ce30d7; one fix after
the first full run (906 s) crashed at its JSON dump on a numpy bool, commit
51889ac — seeds are fixed, so the re-run's numbers are the first run's and
the first run's log is kept as `samples/exhaustive_anneal_run1.sample.txt`.
Run from a temp directory, 3 workers; log `samples/exhaustive_anneal_run.sample.txt`,
numbers `samples/exhaustive_anneal_results.json`.

## What did not hold, first

    Q2 (N=21)  FAILED  mean P_ground over starts does not rise monotonically
                       as cooling slows: 0.334, 0.441, 0.435 at M = 50, 200, 800
    Q3 (N=21)  FAILED  |F| not non-increasing: 405, 301, 317
    -> OUTCOME N=21  NOT_FOUND_IN_RANGE by the pre-registered rule
       (failure set [405, 301, 317] over rates [0.10813, 0.02662, 0.00663]:
       not narrowing-and-persisting)

Both failures are the M = 200 -> 800 step, and both are inside sampling
error: the mean over 512 starts x 20 seeds has sd ~ sqrt(0.44 x 0.56 /
10240) = 0.005, so 0.441 against 0.435 is 1.2 sd; and |F| classifies each
start at P < 0.5 from 20 seeds, so every start with true P near 0.5 flips
between runs at a rate the rule carries no tolerance for. The rule is
reported as written and not amended. Its defect is recorded, the same
defect `SOMS` recorded from the other side: a literal monotonicity test on a
20-seed estimate has no noise band, so it fires on noise (here) or passes
on a start-independent curve (there). A future pre-registration on either
construction needs a tolerance stated in seeds.

## The map (exhaustive; both N)

    N=15  3 cells, 512 states, 57 energy levels; E_min = 0.2 at 16 ground
          states (register pairs (3,5), (5,3) with the spectator free);
          greedy single-flip descent reaches the ground set from 224/512
    N=21  3 cells, 512 states, 57 levels; E_min = 0.0 at 4 ground states
          (pairs (3,7), (7,3), spectator in {1,5}); greedy reaches 288/512

Q1 HELD on both: the ground-set sizes and energies derived in the
pre-registration from the energy formula are what the enumeration finds.

## Anneal table (20 seeds per start, 512 starts; r = ln(200)/(M-1) plays eps)

    N    M     rate      mean P   |F| (P<0.5)   min P   mean P | greedy-ok   mean P | greedy-fails
    15   50    0.10813   0.344      395         0.000        0.494                 0.227
    15   200   0.02662   0.360      375         0.000        0.511                 0.243
    15   800   0.00663   0.365      360         0.000        0.514                 0.249
    21   50    0.10813   0.334      405         0.000        0.435                 0.206
    21   200   0.02662   0.441      301         0.000        0.564                 0.283
    21   800   0.00663   0.435      317         0.000        0.553                 0.282

    OUTCOME N=15  FUNNEL_FOUND (discrete analog) by the rule: |F| narrows
                  395 -> 375 -> 360 and persists at the slowest rate
    OUTCOME N=21  NOT_FOUND_IN_RANGE by the rule (above)

## What the table says beyond the enum

The "failure set" is not thin. At every rate 59-79% of starts have
P_ground < 0.5 and some starts (min P = 0) never reach the ground set in
20 anneals. The paper's funnel is a THIN set of starts reaching the
attractor the reduced model forbids; here the set the rule tracks is the
large complement of the starts that reach the ground state. The enum's
"narrows and persists" condition is met by a large set shrinking slowly,
which is the annealer being weak at these settings (T 2.0 -> 0.01
exponential over 50-800 steps on a 3-cell register), not a thin structure.

What IS start-dependent, and is the sharpest contrast with the SOMS
analog: starts whose greedy single-flip descent ends on the ground set
reach it at roughly twice the rate of starts whose descent ends off it
(0.49-0.56 against 0.21-0.28), at every rate and both N, so Q6 HELD on both.
The initial configuration survives the anneal here where in SOMS it was
erased within one sweep. The difference is the drive: SOMS's slow variable
is state-coupled with a mu0 = 4 head start that orders the chain before the
race is decided; the annealer's temperature schedule is open-loop and at
T_end = 0.01 the chain freezes where it is, so basin membership at the
start carries through. That is a reading of the two tables side by side,
not a pre-registered result.

Slower cooling helps little: mean P moves 0.344 -> 0.365 (N=15) over a
16x change in rate. A 3-cell register at these schedules is close to a
quench; the cooling rate is not the eps of a funnel here, it is a
quench-depth knob.

## landscape_scan against the exhaustive map (Q5 HELD)

    1000 samples, seeds 0-4, replay of the engine's own RNG matches the
    scan's output in every seed (so the comparison is of the same points)
    N=15  exact minimum found 5/5; distinct ground states found
          [15, 14, 15, 14, 13] of 16; configurations never visited
          [68, 79, 72, 70, 78] of 512; energy levels unseen [1, 0, 0, 0, 1]
    N=21  exact minimum found 5/5; distinct ground states [4, 4, 4, 3, 3]
          of 4; never visited [68, 79, 72, 70, 78]; levels unseen [1, 0, 0, 1, 1]

The unvisited counts are identical across N because the scan's RNG draws
configurations independently of N; the same 1000 draws are scored on two
landscapes. What random sampling missed: at least one ground-state
configuration in 5 of 5 seeds (N=15) and 2 of 5 (N=21), and 13-15% of the
state space in every seed — while finding the exact minimum energy every
time. On a 512-state space the minimum is cheap and the ground SET is not.

## CHECK ONLY: `scale_invariance_breakdown.py`

Read, not run against anything; no link is claimed. The module computes
nothing numerical. It carries two dictionaries — five generic breakdown
classes (phase transitions, catastrophe topology, information-theoretic
limits, quantum measurement boundary, symmetry breaking) and a three-tier
proof protocol (metrology, substrate crossover, dimensional frame
exhaustion) — three dataclasses (`CandidateBreakdown`, `FalsifiableClaim`,
`AuditGate`) with no methods, two functions that render the dictionaries
as strings, and an operator note. Whether a slow-fast funnel is an
instance of any of its five classes is a question the module gives no
procedure for deciding; by its own tier 2 the cooling-rate analog here is a
substrate change (open-loop schedule for a state-coupled variable) before
it is a scale-invariance anything.

## Pre-registered predictions

    HELD    Q1  ground sets 16 at E=0.2 (N=15), 4 at E=0 (N=21)
    HELD    Q2  N=15 mean P rises with slower cooling: 0.344, 0.360, 0.365
    FAILED  Q2  N=21: 0.334, 0.441, 0.435
    HELD    Q3  N=15 |F| non-increasing: 395, 375, 360
    FAILED  Q3  N=21: 405, 301, 317
    HELD    Q4  |F| > 0 at the slowest rate, both N
    HELD    Q5  scan misses >= 1 ground state in >= 1 of 5 seeds (N=15);
                finds E_min 5/5 for both N
    HELD    Q6  greedy-fails starts have lower mean P than greedy-ok starts
                at the fastest rate, both N

Scope: stochastic (Metropolis annealer, `np.random.seed` fixed per anneal),
M in {50, 200, 800}, T 2.00 -> 0.01 exponential, 20 seeds per start, all
512 starts; MandalaComputer(golden_depth=2) = 3 cells, factorization
encoding with coupling scaled 0.1; DISCRETE state space, OPEN-LOOP slow
drive; one parameter set. Nothing here is a statement about factoring or
about the paper's continuous system.
