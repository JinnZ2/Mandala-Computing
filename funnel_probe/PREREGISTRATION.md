# PRE-REGISTRATION — funnel_probe/ (Mandala-Computing)

WORK ORDER: singular-funnel probes, 4 repos (Kavik via Claude, 2026-10-01).
Source under test: Yanchuk, Wieczorek, Jardon-Kojakhmetov, Alkhayuon,
PRL 137, 147202 (2026); arXiv:2601.02001.
Committed BEFORE any probe code exists in this folder. No root module is
edited. `quantum_mandala.py` is EXCLUDED (different mathematics).
Run artifacts go to a temp directory.

LABEL: discrete state space; the annealer's cooling rate stands in for eps
and is an OPEN-LOOP drive (reads the step counter, not the state), so this
is a slow-parameter analog, not the paper's state-coupled slow variable.

## Outcome enum

    FUNNEL_FOUND         a set of initial states that fails to reach the
                         ground state, shrinking as the cooling rate falls
                         (slower cooling = smaller eps) and non-empty at
                         the slowest rate
    NOT_FOUND_IN_RANGE   the failure set is empty at every rate, or does
                         not shrink across the rate grid (grid printed)
    NOT_IN_CLASS         the engine has no slow variable (not the case:
                         the schedule is one, open-loop; labelled above)
    INCONCLUSIVE         not applicable here: every anneal runs to its
                         fixed step count

## Construction

    engine   MandalaComputer(golden_depth=2, temperature=1.0)
             .encode_factorization(N), N in {15, 21}
             -> bloom gives 1 + 2 = 3 cells; digits_per_factor = 1;
             cells_per_pair = 2; ONE register pair (cells 0, 1) and one
             FRET-coupled spectator (cell 2). Asserted at run time.
             (No golden_depth gives exactly 2 cells; depth 2 is the
             smallest bloom holding a factor pair.)
    states   all 8^3 = 512 initial configurations, enumerated
    exact    `compute_total_energy` on all 512 -> the exact landscape;
             ground set = argmin. Derived now from the energy formula:
               N=15: factor pairs (3,5),(5,3) -> states (1,3),(3,1);
                     pair coupling 0.1*sin^2(2*pi/4) = 0.1; spectator adds
                     0.1 for every s2 (the two sin^2 arguments differ by
                     pi/2) -> 16 ground states at E = 0.2
               N=21: pairs (3,7),(7,3) -> states (1,5),(5,1); pair
                     coupling 0 (diff 4 -> sin^2(pi) = 0); spectator 0 iff
                     s2 in {1,5} -> 4 ground states at E = 0
             These counts are a prediction (Q1) the enumeration checks.
    anneal   simulated_annealing(max_steps=M, T_start=2.0, T_end=0.01,
             schedule="exponential"); cooling rate r = ln(200)/(M-1) per
             step plays eps:  M in {50, 200, 800} -> r = 0.108, 0.0266,
             0.00663. Start: cell states set to the enumerated config;
             np.random.seed(seed) immediately before each anneal,
             seed = N*10^6 + M_idx*10^5 + config_idx*32 + k, k = 0..19
             (20 seeds per start per rate). stdout of the engine discarded.
    success  final energy == exact minimum (equivalently a verified factor
             pair plus minimal coupling)
    readout  P_ground(start, r); FAILURE SET F(r) = starts with
             P_ground < 0.5; |F(r)|; mean P_ground over starts vs r;
             P_ground vs the start's exact energy rank
    random   `landscape_scan(num_samples=1000)` with np.random.seed(s),
             s in 0..4, per N: min energy, best_config, number of distinct
             ground-state configurations found (vs 16 / 4), number of the
             512 configurations never visited, energy levels never seen.
             "What random sampling missed" = those three differences.

Pre-registered predictions:
    Q1  ground-set sizes 16 (N=15) and 4 (N=21), energies 0.2 and 0
    Q2  mean P_ground over starts increases as r falls (slower cooling)
    Q3  |F(r)| is non-increasing as r falls
    Q4  |F(r)| > 0 at the slowest rate r = 0.00663 (persists) — weakest
    Q5  with 1000 samples, landscape_scan misses at least one ground-state
        configuration in >= 1 of 5 seeds for N=15 (expected miss
        probability per seed ~0.91) and finds the exact minimum energy in
        all 5 seeds for both N
    Q6  a single-flip local-minimum analysis of the exact landscape
        predicts which starts are in F: starts whose single-flip descent
        path (greedy) ends off the ground set have lower P_ground at the
        fastest rate than those whose path ends on it

CHECK ONLY (no run, no claim of a link): `scale_invariance_breakdown.py`
is read and what it computes is reported in RESULTS.md.

## Step 1 — reference + noise (shared across the four repos, identical text)

Reference: `singular_funnel_pitchfork.py` vendored UNCHANGED (sha256 recorded
below). Step 0 result on this machine before any repo work: selftest 4/4 PASS,
STATUS REPRODUCED, mu0=4 eps=0.1 edge log10 x0* = -7.30, slope
d(ln x0*)/d(1/eps) = -1.616. Matches the order's expected values.

Noise script `funnel_noise.py` (stdlib only), Euler-Maruyama, dt = 0.01,
T_max = 600, a = 3, b = 2, eps = 0.1, mu0 = 4.

    model (a)  additive on x, reflecting at x = 0:
               x  <- |x + x(mu - x^2) dt + sigma sqrt(dt) xi|
               mu <- mu + eps(-mu + a x - b) dt
    model (b)  additive on mu, x integrated as y = ln x (deterministic):
               y  <- y + (mu - x^2) dt
               mu <- mu + eps(-mu + a x - b) dt + sigma sqrt(dt) xi

Absorbing exits (declared before any run; differ from the reference's because
the e0 test `x < 1e-8` is not meaningful under x-noise of that size):
    e0  : mu < -0.5 and x < 0.1
    e2  : x > 1.0
    INCONCLUSIVE : neither reached by T_max

Grid:
    starts     mu0 = 4, x0 in {1e-9, 10^-8.5, 1e-8}   (all inside the
               deterministic funnel, whose edge at mu0=4, eps=0.1 is 10^-7.30)
    sigma (a)  10^-11, 10^-10.5, ..., 10^-6      (11 values)
    sigma (b)  10^-4, 10^-3.5, ..., 10^0         (9 values)
    runs       200 per (model, start, sigma); seed = 7919*model_idx
               + 1009*start_idx + 101*sigma_idx + run_idx; random.Random(seed)
    readout    P(e0) with a Wilson 95% interval; sigma_half = the log-
               interpolated sigma at which P(e0) first falls to <= 0.5 of
               P(e0) at the smallest sigma on the grid, per (model, start)

Pre-registered predictions (checked, not tuned):
    P1  at the smallest sigma, P(e0) >= 0.95 for every start (noise
        negligible; reproduces the deterministic funnel)
    P2  P(e0) is non-increasing in sigma up to sampling noise (no rise
        larger than 0.10 between adjacent grid points)
    P3  model (a): sigma_half in [1e-9, 1e-7] (noise competes directly
        with a funnel of width ~5e-8 in x)
    P4  model (b): sigma_half in [1e-2, 1] (noise enters x only through
        the time integral of mu; margin to the edge is ~3.9 nats of ln x)
    P5  sigma_half(b) / sigma_half(a) > 1e4
    P6  within one model, sigma_half across the three starts agrees to
        within a factor of 3 (the width, not the depth, sets survival)

Outcome enum for this step:
    FUNNEL_FOUND         P1 holds and sigma_half lies inside the grid
    NOT_FOUND_IN_RANGE   P(e0) never halves inside the grid (range printed)
    NOT_IN_CLASS         not applicable: this is the paper's own system
    INCONCLUSIVE         > 5% of runs at any grid point used for the
                         decision hit T_max unclassified

vendored reference sha256: 466629a741722183a09221a1594c8f75db7d922ce00eede3afd8e7f01c1f9c46

Scope on every result: stochastic (Metropolis annealer), fixed seeds;
parameter set as above; DISCRETE state space, open-loop slow drive.
A null is a result.
