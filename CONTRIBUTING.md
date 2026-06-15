# Contributing to Concord Protocol

Concord accepts changes that improve reusable multi-agent governance, contract integrity, domain separation, verification, and recovery semantics.

## Before proposing a change

A protocol proposal must:

1. Describe a real failure mode or interoperability gap.
2. Be reusable beyond one project, model, agent, vendor, or tool.
3. State whether the change is breaking or backward compatible.
4. Define acceptance criteria and a verification plan.
5. Describe security boundaries and failure recovery.

Project-specific workflows, prompts, channel policies, credentials, and business facts belong in the adopting project, not in Concord.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Validate an individual Guarded Upload contract:

```bash
python3 tools/validate_guarded_upload_contract.py /path/to/task_contract.json
```

## Proposal process

1. Open a Protocol Proposal using the issue template.
2. Add schemas, compatibility notes, and tests when the shape is concrete.
3. Obtain review from at least two distinct contributors or agents covering different committee seats.
4. Resolve security and migration objections.
5. Merge with a version and changelog update.

See [GOVERNANCE.md](GOVERNANCE.md) for committee responsibilities.

## Pull-request checklist

- [ ] No credentials, private contracts, production artifacts, or machine-local paths.
- [ ] JSON Schemas reject unknown properties where strict contracts are intended.
- [ ] Cross-field rules are implemented outside Schema when Schema cannot express them safely.
- [ ] Positive and negative tests are included.
- [ ] Security limitations are stated without claiming sandbox enforcement.
- [ ] README, SECURITY, and CHANGELOG are updated when public behavior changes.

## Commit scope

Keep protocol, runtime implementation, and project facts in separate commits and repositories. Concord may include examples, but examples must contain synthetic data only.
