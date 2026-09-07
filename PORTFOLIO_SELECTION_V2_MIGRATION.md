# Portfolio Selection v2 corrective migration

Status: executable corrective plan.

This document supersedes completion claims for the Portfolio Selection v2 migration where current production code does not yet satisfy the frozen PR454-PR459 semantics. Historical backlog entries remain audit history; the executable corrective sequence is PR461-PR480 below.

Baseline SHA: `d71548b6328553e6a1c8747a3692ba4220f6f786`.

## 1. Verified baseline gaps

The corrective series starts from these concrete current-runtime facts:

- the production candidate/validation path is still seeded from one `LW_FULL` risk model;
- `multivariate_risk_model_comparison.py` still behaves as a shadow manifest and persists comparison split rows as `scheduled` rather than measured OOS evidence;
- the production Decision is still selected from the legacy candidate/scorecard path rather than the 14-configuration comparison evidence;
- the default validation policy still exposes a 100-observation minimum-training value while the frozen Selection v2 comparison policy requires 252 observations;
- full-sample performance/risk-contribution persistence is still driven from the original candidate set rather than the complete 14-configuration family;
- current closeout tests prove several static invariants but do not yet prove the complete numerical, lineage, authority, restart and browser behavior required for a real Selection v2 PASS.

No PR in this series may claim Portfolio Selection v2 complete until PR480 produces PASS evidence on the exact final head.

## 2. Frozen end-state

The production workflow must be exactly:

`current Univariate selection -> matching successful Bivariate evidence -> requested objective -> 14 semantic allocator x risk-spec configurations -> one common chronological OOS schedule -> split-local risk-model fits -> split-local portfolio refits -> common-split validation -> deterministic objective ranking -> Decision v2 -> full-current-sample refit of the exact 14-family -> exact winning fitted portfolio -> descriptive diagnostics`.

Production objectives remain exactly:

- `return_risk`;
- `return_drawdown`;
- `minimum_risk`.

Frozen comparison family remains exactly 14 configurations:

- Equal Weight @ `LW_FULL` = 1;
- Inverse Volatility @ `LW_FULL`, `LW_ROLLING_252`, `EWMA_094` = 3;
- Minimum Variance @ all 3 specs = 3;
- Equal Risk Contribution @ all 3 specs = 3;
- Hierarchical Risk Parity @ all 3 specs = 3;
- Minimum CVaR @ `LW_FULL` = 1.

Frozen common OOS policy:

- minimum training observations = 252;
- test window observations = 21;
- maximum refits = 8;
- minimum completed common splits = 2;
- all 14 configurations use identical chronological split starts and test windows;
- `LW_FULL` uses all observations available strictly before the test window;
- `LW_ROLLING_252` uses the exact trailing 252 common observations strictly before the test window;
- `EWMA_094` uses all observations available strictly before the test window with decay 0.94;
- a split-local worker fits at most three risk models and reuses them across allocator configurations;
- unavailable configuration/split evidence is persisted and never silently dropped;
- full-history/current-sample evidence is descriptive and cannot enter ranking.

## 3. Migration evidence contract

Every QA PR in this series must emit/update a sanitized machine-readable `portfolio-selection-v2-migration@v1` evidence artifact. It must contain at least:

- exact Git SHA under test;
- migration stage and stage ordinal;
- completed implementation PRs;
- completed QA PRs;
- current selection authority (`legacy_lw_full`, `shadow_14_config`, `common_oos_14_config`);
- comparison configuration count;
- comparison split policy fingerprint;
- whether split-local three-spec risk fits are implemented;
- whether 14 split-local candidates are implemented;
- whether common OOS metrics are measured;
- whether config-keyed scorecards are authoritative;
- whether Decision v2 consumes common OOS ranking;
- whether all 14 full-sample fits are materialized;
- whether Decision -> configuration -> candidate -> risk model -> performance -> risk contribution joins are exact;
- whether checkpoint/resume is compatible with current execution version;
- whether Dash consumes only persisted selection evidence for ranking display;
- whether legacy/shadow authority is retired;
- focused test/gate references;
- sanitized failure reasons when stage is not PASS.

QA PRs are evidence-only. They may add tests, fixtures, or evidence assemblers, but must not fix production behavior. A discovered defect requires a separate corrective implementation PR before the QA PR is rerun.

## 4. Executable corrective sequence

### PR461 - Freeze one canonical 14-configuration comparison contract

Branch: `refactor/pr461-selection-v2-comparison-contract`

Priority: P0 contract correctness.

Owned paths: narrow comparison-policy/configuration modules, contract documentation, focused contract tests. No Decision or Dash behavior change.

Task:

- introduce one canonical Selection v2 comparison policy with exact `252/21/8/2` semantics;
- make the 14 semantic configurations first-class immutable definitions with stable configuration IDs;
- prohibit the production comparison coordinator from importing the legacy 100-observation default as its authority;
- encode which methods are covariance-spec-sensitive and therefore receive three specs;
- keep Equal Weight and Minimum CVaR single-spec by contract;
- expose deterministic configuration ordering and split-policy fingerprinting.

Acceptance:

- exactly 14 unique configuration IDs exist in deterministic order;
- family counts are exactly `1,3,3,3,3,1` in the frozen method order;
- comparison policy is exactly 252 training, 21 test, maximum 8 refits, minimum 2 completed splits;
- changing legacy `DEFAULT_WALK_FORWARD_POLICY.minimum_training_observations` cannot alter the Selection v2 comparison policy;
- configuration ID changes if method or risk-spec identity changes and does not change for fit dates/weights;
- unsupported method/spec combinations fail closed;
- no production selection authority changes in this PR.

### PR462 - QA stage 1: comparison-contract migration evidence

Branch: `test/pr462-selection-v2-comparison-contract-qa`

Priority: P0 migration QA.

Depends on: PR461.

Task:

- independently enumerate the 14 expected method/spec pairs;
- independently derive expected chronological split starts for boundary-sized calendars;
- verify stable ordering/fingerprints and fail-closed unsupported pairs;
- publish migration stage `comparison_contract_frozen`.

Acceptance:

- independent oracle equals the exact 14 production definitions;
- calendars at 251, 252, 272, 273 and large-sample boundaries produce contract-correct eligibility/splits;
- worker count cannot affect configuration/split ordering;
- evidence records selection authority is still not yet `common_oos_14_config`;
- no production source changes.

### PR463 - Build shared split-local risk-model fit bundles

Branch: `feat/pr463-selection-v2-split-risk-models`

Priority: P0 empirical correctness.

Depends on: PR462.

Owned paths: risk-model comparison coordinator, risk-model fit helper, focused tests. No candidate ranking or Decision switch.

Task:

- for every common OOS split, fit exactly the required `LW_FULL`, `LW_ROLLING_252`, and `EWMA_094` training-only risk models;
- reuse each fitted model across all configurations consuming that spec;
- persist split index, train/test boundaries, spec key/id, risk-model ID and fit-calendar ID;
- persist unavailable risk-model fits explicitly;
- prohibit test/future observations from any fit input.

Acceptance:

- at most three risk-model fits occur per comparison split;
- all fits end strictly before `test_start`;
- rolling specification contains exactly 252 common training observations when available;
- full and EWMA specs consume all available common training observations and no test observations;
- all three spec identities and fit calendars are persisted per split;
- future-row mutation cannot change an already prior split fit;
- sequential and multi-worker output is byte-equivalent after normalization;
- no candidate ranking or Decision change.

### PR464 - QA stage 2: split-risk-model numerical and leakage QA

Branch: `test/pr464-selection-v2-split-risk-models-qa`

Priority: P0 migration QA.

Depends on: PR463.

Task:

- build independent small-matrix covariance oracles for all three specs;
- mutate future/test rows and prove prior fits remain unchanged;
- instrument fit-call counts;
- publish migration stage `split_risk_models_complete`.

Acceptance:

- independent covariance/fit-calendar oracle matches production within existing deterministic numerical tolerances;
- exactly three-or-fewer risk fits occur per valid split, never one fit per configuration;
- rolling windows are exact trailing 252 observations;
- future/test mutation invariance passes;
- unavailable fits remain represented;
- no production source changes.

### PR465 - Assemble the exact 14 split-local candidate family

Branch: `feat/pr465-selection-v2-split-candidates`

Priority: P0 configuration completeness.

Depends on: PR464.

Owned paths: comparison coordinator and narrow candidate-family assembly helper. No ranking or Decision switch.

Task:

- consume the shared split-local risk-model bundle and build only the 14 contract-permitted candidate configurations;
- preserve stable configuration ID while candidate/risk IDs remain fit-specific;
- avoid constructing redundant Equal Weight and Minimum CVaR variants for non-`LW_FULL` specs;
- persist unavailable candidates per split/configuration rather than dropping them;
- keep configuration-keyed collections throughout.

Acceptance:

- each valid split has exactly 14 candidate slots, including unavailable slots;
- configuration IDs are stable across refits while candidate IDs and risk-model IDs may change;
- each configuration references the exact split-local risk spec and fit calendar;
- no dictionary/list collection may overwrite same-method different-spec candidates;
- Equal Weight and Minimum CVaR each appear once per split;
- worker count cannot change output order/content;
- no ranking or Decision change.

### PR466 - QA stage 3: split-candidate identity and completeness QA

Branch: `test/pr466-selection-v2-split-candidates-qa`

Priority: P0 migration QA.

Depends on: PR465.

Task:

- independently map all 14 configuration IDs to method/spec identities across at least three refits;
- prove no method-key overwrite or duplicate semantic configuration;
- publish migration stage `split_candidate_family_complete`.

Acceptance:

- exact 14 slots exist on every scheduled split;
- stable configuration identity vs fit-specific candidate/risk identity is demonstrated across at least three refits;
- unavailable candidates remain joinable to configuration/split identity;
- duplicate configuration IDs fail deterministically;
- no production source changes.

### PR467 - Measure canonical common-split OOS validation for all 14 configurations

Branch: `feat/pr467-selection-v2-common-oos-validation`

Priority: P0 empirical evidence.

Depends on: PR466.

Owned paths: comparison coordinator, canonical validation adapter, persistence/checkpoint phase only where needed. No Decision switch.

Task:

- evaluate every split-local candidate on the exact common 21-observation test window;
- reuse canonical return, volatility, Sharpe, Sortino, CVaR, max-drawdown and same-split return/drawdown arithmetic;
- compute turnover by semantic configuration identity across chronological refits;
- apply the existing production transaction-cost rate after turnover;
- persist complete/unavailable validation rows keyed by split + configuration + fit identity;
- ensure all 14 configurations are evaluated against the same split schedule.

Acceptance:

- measured OOS rows replace `scheduled` placeholders as the comparison evidence source;
- each configuration has one validation status per common split;
- test boundaries are identical across all 14 configurations;
- first allocation turnover and subsequent turnover preserve canonical semantics;
- no future rows enter training or test metrics for an earlier split;
- missing/unavailable candidate produces explicit unavailable evidence;
- validation ordering is chronological and worker-invariant;
- Decision still uses the old authority until PR471.

### PR468 - QA stage 4: common-OOS return, turnover and split reconciliation QA

Branch: `test/pr468-selection-v2-common-oos-validation-qa`

Priority: P0 migration QA.

Depends on: PR467.

Task:

- independently calculate selected small OOS portfolio returns, transaction costs, turnover, Sharpe and drawdown ratios;
- reconcile every configuration to the common split calendar;
- publish migration stage `common_oos_measured`.

Acceptance:

- independent OOS numerical oracle matches persisted validation rows;
- all 14 configs share exact test boundaries;
- config-specific turnover state never leaks across risk specs or methods;
- future-row mutation cannot alter prior validation evidence;
- unavailable/missing evidence remains explicit and countable;
- no production source changes.

### PR469 - Build authoritative configuration-keyed scorecards and ranking evidence

Branch: `feat/pr469-selection-v2-config-ranking-evidence`

Priority: P0 ranking correctness.

Depends on: PR468.

Owned paths: scorecard aggregation/ranking coordinator and narrow contracts. No Decision switch.

Task:

- aggregate scorecards by configuration ID rather than fit-specific candidate ID;
- require exact common-split completeness for rankability;
- preserve non-blocking `cash_flow_evidence_only` warning semantics;
- implement the frozen objective metrics from common OOS evidence only;
- preserve deterministic tie-break ordering;
- persist ordered ranking evidence for all configurations including unrankable reasons;
- prohibit full-sample/descriptive fields from ranking input.

Acceptance:

- `return_risk` primary metric is median common-split OOS Sharpe;
- `return_drawdown` primary metric is median of same-split post-cost-return / absolute-max-drawdown ratios;
- `minimum_risk` uses the frozen OOS risk metric and direction defined by the existing Decision contract;
- incomplete common-split evidence is unrankable with explicit reason;
- warnings do not become blockers;
- every deterministic tie-break level is explicit and stable;
- ranking accepts only `selection` evidence inputs;
- full-history/current-allocation/structure evidence cannot affect ordering;
- Decision authority remains unchanged until PR471.

### PR470 - QA stage 5: independent objective-ranking oracles

Branch: `test/pr470-selection-v2-config-ranking-qa`

Priority: P0 migration QA.

Depends on: PR469.

Task:

- construct independent fixtures where `LW_FULL`, `LW_ROLLING_252`, and `EWMA_094` each win through OOS evidence;
- independently calculate all three objective primaries and tie-breaks;
- verify warning/blocking and incomplete-evidence semantics;
- publish migration stage `config_ranking_ready`.

Acceptance:

- each of the three risk specs can be the winning spec in a controlled fixture for a spec-sensitive allocator;
- no alternate spec can win because of full-sample performance;
- independent metric/tie-break oracle equals production order;
- deleting one required split makes that configuration unrankable;
- restricting all configs to `LW_FULL` reproduces the predecessor method-ranking semantics on compatible fixtures;
- no production source changes.

### PR471 - Cut production Decision v2 over to the common-OOS 14-configuration authority

Branch: `feat/pr471-selection-v2-decision-authority-cutover`

Priority: P0 production authority.

Depends on: PR470.

Owned paths: Multivariate compute selection orchestration, Decision contract/persistence, narrow tests. No Dash redesign.

Task:

- make the configuration ranking from PR469 the sole production winner authority;
- stop invoking the legacy six-method `LW_FULL` scorecard path as a ranking authority;
- preserve requested objective exactly from run request to Decision;
- persist winner configuration ID, method, risk-spec key/id, comparison split count, primary metric, tie-breaks, warnings/blockers and production eligibility;
- never fall back to another method/spec if the selected configuration cannot be reconciled later;
- bump execution/checkpoint version if required by changed persisted semantic objects.

Acceptance:

- exactly one canonical OOS selection authority exists in production;
- Decision winner comes from the 14-configuration common-split ranking;
- all three requested objectives reach Decision unchanged;
- unavailable/unrankable configurations cannot win;
- no in-sample/full-history metric is consumed by winner selection;
- no silent fallback exists;
- legacy six-method validation may remain only if demonstrably descriptive/non-authoritative pending retirement PR479.

### PR472 - QA stage 6: production-authority cutover QA

Branch: `test/pr472-selection-v2-decision-authority-qa`

Priority: P0 migration QA.

Depends on: PR471.

Task:

- instrument/cross-check the sole ranking call path;
- prove each objective can choose the expected configuration;
- prove legacy scorecards cannot perturb Decision;
- publish migration stage `common_oos_authority_live`.

Acceptance:

- mutation of legacy/full-history descriptive artifacts leaves Decision unchanged;
- mutation of common OOS ranking evidence changes Decision when and only when ranking semantics require it;
- exactly one selection authority is reachable from production compute;
- Decision lineage names the exact winning configuration/spec;
- no production source changes.

### PR473 - Materialize and persist the exact full-sample 14-configuration family

Branch: `feat/pr473-selection-v2-full-sample-family`

Priority: P0 winner reconciliation and diagnostics.

Depends on: PR472.

Owned paths: full-sample comparison/refit coordinator, candidate/performance/risk-contribution persistence. No ranking changes.

Task:

- after OOS ranking, fit at most three current-sample risk models and materialize the exact 14 contract configurations;
- persist all successful/unavailable current-sample candidates with configuration/spec/risk/fit lineage;
- build performance and risk-contribution evidence for all feasible configurations without method-key overwrites;
- reconcile the Decision winner to the exact current-sample candidate of the winning configuration;
- mark current-sample performance, allocation, risk contributions, matrix stress and structure as `descriptive`;
- if exact winning configuration cannot fit current input, Decision becomes unavailable/ineligible with no fallback.

Acceptance:

- current-sample family contains exactly 14 configuration slots;
- at most three current-sample risk models are fit and reused;
- Decision -> configuration -> fitted candidate -> fitted risk model -> fit calendar is exact;
- exact winner has corresponding performance and risk-contribution evidence when feasible;
- same-method different-spec performance series coexist and remain distinguishable;
- all current-sample evidence is excluded from ranking inputs;
- no fallback portfolio is promoted if winner refit fails.

### PR474 - QA stage 7: full lineage and evidence-role reconciliation

Branch: `test/pr474-selection-v2-lineage-qa`

Priority: P0 migration QA.

Depends on: PR473.

Task:

- independently join Decision through all persisted current-sample artifacts;
- prove 14-config coexistence and evidence-role boundaries;
- publish migration stage `full_sample_lineage_complete`.

Acceptance:

- no orphan winner/config/candidate/risk IDs;
- exact Decision winner joins to one current-sample candidate and its exact risk model, performance series and risk-contribution set;
- same method under different specs never collides;
- `selection` vs `descriptive` evidence roles are machine-verifiable;
- deleting or mutating descriptive evidence cannot change ranking/Decision;
- no production source changes.

### PR475 - Harden checkpoint/resume across the new selection phases

Branch: `fix/pr475-selection-v2-checkpoint-migration`

Priority: P0 operational correctness.

Depends on: PR474.

Owned paths: Multivariate checkpoint state/versioning, phase/progress orchestration, restart tests.

Task:

- checkpoint/restore split-risk fits, split-candidate family, measured OOS validation, ranking evidence, Decision and full-sample family at explicit phase boundaries;
- reject pre-cutover or incompatible execution-version checkpoints before semantic objects are reused;
- reject corrupt or phase-inconsistent checkpoints and recompute cleanly;
- keep progress monotone with updated phase totals;
- make repeated resume/publication idempotent.

Acceptance:

- clean and resumed runs produce identical normalized selection/Decision/full-sample artifacts;
- every supported resume boundary is exercised;
- old-version checkpoints are ignored safely;
- corrupt checkpoints trigger clean recomputation rather than partial semantic reuse;
- repeated publication is idempotent;
- progress is monotone and phase count is synchronized with production orchestration.

### PR476 - QA stage 8: restart-equivalence migration QA

Branch: `test/pr476-selection-v2-checkpoint-qa`

Priority: P0 migration QA.

Depends on: PR475.

Task:

- independent clean-vs-resumed artifact reconciliation at every supported phase;
- corrupt/version-mismatch restart tests;
- publish migration stage `checkpoint_resume_complete`.

Acceptance:

- normalized artifacts and Decision are identical for clean and every supported resumed run;
- no old semantic checkpoint object survives a version mismatch;
- no duplicate artifacts appear after repeated resume/publication;
- no production source changes.

### PR477 - Cut Dash/read models over to Selection v2 evidence

Branch: `feat/pr477-selection-v2-dash-cutover`

Priority: P1 product correctness.

Depends on: PR476.

Owned paths: Multivariate Dash page, read/presenter adapters, focused browser fixtures. No financial recomputation in browser code.

Task:

- render `Selection Evidence` from persisted common-OOS 14-config ranking evidence;
- render `Portfolio Diagnostics` from descriptive current-sample artifacts;
- make OOS and performance series configuration/spec aware;
- display Decision objective, metric, method, risk spec, split count, tie-breaks, warnings and blockers;
- render `Final Portfolio` only when Decision is available and production-eligible and exact winner diagnostics exist;
- otherwise render explicit no-production-portfolio state; any feasible preview remains `Candidate Preview - not selected`;
- preserve exact objective submission and stale-upstream readiness rules;
- expose no allocator/spec/manual winner control.

Acceptance:

- each objective is submitted exactly and rendered from persisted Decision evidence;
- same-method different-spec OOS/performance series are distinguishable;
- Selection Evidence and Portfolio Diagnostics are visibly separated;
- stale Selection/Bivariate lineage disables execution;
- unavailable/ineligible Decision never renders a preview as Final Portfolio;
- browser code does no portfolio/risk/score recomputation.

### PR478 - QA stage 9: browser and end-to-end migration QA

Branch: `test/pr478-selection-v2-browser-qa`

Priority: P1 migration QA.

Depends on: PR477.

Task:

- exercise all three objective requests through the live page fixture;
- test same-method multi-spec rendering, stale readiness, ineligible Decision, exact winner diagnostics and console safety;
- publish migration stage `dash_cutover_complete`.

Acceptance:

- all three objectives reach the job request and Decision exactly;
- no hard-coded objective substitution exists;
- no manual allocator/spec/winner control exists;
- stale upstream state blocks execution;
- exact winning config/spec is rendered consistently across Decision and diagnostics;
- no page/console errors at supported viewport fixtures;
- no production source changes.

### PR479 - Retire shadow/legacy Selection v2 authority and synchronize contracts

Branch: `refactor/pr479-selection-v2-legacy-retirement`

Priority: P1 cleanup and governance.

Depends on: PR478.

Owned paths: obsolete comparison/legacy-ranking code, stale tests, CONTRACTS/ARCHITECTURE/BACKLOG/DECISIONS/GATES only where semantics changed, merge-gate workflow if needed.

Task:

- remove or rename shadow-only comparison semantics so production names match measured common-OOS behavior;
- delete unreachable legacy ranking code and tests that imply a second authority;
- preserve only explicit compatibility/read migration needed for historical artifacts;
- synchronize contract/execution documentation with the final runtime;
- ensure merge-gate covers the complete Selection v2 test surface and exact final head; add `push: main` verification if absent and compatible with repository CI policy;
- do not redesign allocators, max-weight policy, expected returns, CVaR scenarios or Bivariate visualization.

Acceptance:

- code search finds one and only one production selection authority;
- no production artifact named/labelled `shadow` represents authoritative Selection v2 evidence;
- no retired allocator or legacy selection path can re-enter current read/ranking models;
- docs and contracts describe actual runtime, not intended future state;
- focused unit/integration/browser suites are included in merge-gate coverage;
- no unrelated financial-model changes.

### PR480 - Final independent Portfolio Selection v2 closeout and immutable PASS evidence

Branch: `test/pr480-selection-v2-final-closeout`

Priority: P0 final QA/PASS.

Depends on: PR479.

Owned paths: tests, QA evidence assembler, synchronized QA docs only. No production fixes.

Task:

Produce one immutable sanitized `portfolio-selection-v2` PASS artifact on the exact head SHA. It must contain the final `portfolio-selection-v2-migration@v1` record with stage `complete` and all prior QA references.

Acceptance must independently prove:

- exactly six allocator methods and exactly 14 semantic method/spec configurations;
- exact 252-train / 21-test / maximum-eight-refit common schedule;
- split-local risk models are training-only and at most three fits per split;
- all 14 split-local candidate slots exist without configuration overwrite;
- measured common OOS validation is configuration-keyed and chronologically identical across configs;
- future-data mutation cannot alter prior fit or OOS evidence;
- independent numerical oracles reconcile representative covariance, portfolio return, turnover, transaction cost, Sharpe, max drawdown and return/drawdown calculations;
- warning/blocking semantics including non-blocking `cash_flow_evidence_only`;
- `return_risk`, `return_drawdown` and `minimum_risk` objective rankings match independent oracles;
- every deterministic tie-break level;
- each risk spec can win only through common OOS evidence;
- incomplete common-split configuration is unrankable;
- exactly one canonical production OOS selection authority;
- requested objective remains unchanged from UI/job request through Decision;
- Decision joins to exact winning full-sample configuration/candidate/risk model/fit calendar/performance/risk contributions;
- all 14 current-sample configuration slots coexist and descriptive evidence never enters ranking;
- current winner refit failure produces unavailable/ineligible Decision with no fallback;
- clean/resumed execution is artifact-equivalent and publication-idempotent;
- live Dash renders configuration/spec-aware Selection Evidence and Portfolio Diagnostics with no console/page errors;
- no manual allocator/spec/winner selector exists;
- legacy/shadow ranking authority is unreachable/retired;
- repository quality commands and GitHub merge-gate pass on the exact PASS SHA;
- PASS evidence contains no credentials, DSNs, private paths or raw market rows.

PR480 must fail rather than weaken an oracle or acceptance condition. Any failure requires a corrective implementation PR and a fresh PR480 run.

## 5. Explicitly deferred work

The corrective migration must not expand scope into:

- `max_weight = 0.20` redesign or exact-five-holdings behavior;
- Maximum Sharpe or expected-return optimizers;
- Black-Litterman, factor, momentum or regime-conditioned expected-return priors;
- HERC/NCO or additional allocation methods;
- CVaR scenario-generation redesign;
- transaction-cost-aware daily Sharpe reconstruction beyond the frozen current OOS semantics;
- structural PCA/cluster metrics as ranking objectives or hard constraints;
- Optuna/hyperparameter search;
- saved-portfolio / `portfolio.snapshot` / PDF / `.portfell` export-import workflow;
- Bivariate visualization redesign.

## 6. Completion rule

Portfolio Selection v2 is complete only after PR480 PASS on the exact merged runtime head. Intermediate QA stages verify migration progress but are not release-level PASS evidence.