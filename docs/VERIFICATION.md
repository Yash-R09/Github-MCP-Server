# Verification report - 5 November 2026

## Current local checks

- 26 pytest tests passed, including the existing GitHub retry tests, evaluator fixture/boundary/error/CLI tests and a real local stdio MCP catalog integration test for all 21 tools.
- Fixture demonstrations: 50/50 passes; 45/50 passes; 44/50 fails; 49 correct plus one API error fails. These are deterministic logic tests, not model quality scores.
- Python compileall passed for app, client, evaluation and tests.
- pip check: no broken requirements found.
- Terraform fmt -check and validate passed.
- git diff --check passed. Changed-file credential pattern scan found no matches; .env, Terraform state/tfvars and live result output remain ignored. This is a targeted check, not a full historical secret audit.
- No formatter/linter is configured. Docker executable exists but the engine pipe is unavailable, so no image build was verified.

## Latest verified live evaluation

The full run passed at 05 November 2026, 18:52:09 IST (2026-11-05T13:22:09.136465+00:00 UTC). The authenticated Groq model list confirmed account access to `openai/gpt-oss-20b`. Settings: temperature 0, seed 42, low reasoning effort, 4096-token completion budget and strict JSON-schema output.

| Measure | Result |
|---|---:|
| Total cases | 50 |
| Correct | 49 |
| Wrong tool | 1 |
| API/parsing errors | 0 |
| Pass rate | 98.0% |
| Required threshold | 90% |
| Gate | PASS (exit 0) |

Remaining wrong selection: case 29: expected `get_branch`, selected `list_commits`. The dataset and expected answer were preserved. The passing run had zero API errors and used the same evaluator settings as the previous failed run. No fixture predictions replaced live outputs. One passing run does not guarantee future model quality or API availability; every release must execute a fresh evaluation.

The full live report is local ignored `evaluation/results.json`; legacy `evaluation/predictions.json` is preserved and never trusted as release evidence. Dataset SHA256: `625b9f7a4596c0fa9e90cb03137ba46ec8c3d8d625df7e67cda24f749df816e6`. Catalog SHA256: `c08604aff5b215f1330c44d1e73d62f6167c25e617039bd2040b81da3537fdd5`.

### Earlier failures and follow-up fixes

Earlier engineering runs failed with 45/50 correct plus five provider errors, 44/50 plus six errors, and 46/50 plus three rate-limit errors and one wrong answer. A later owner-run evaluation reached 49/50 but had one BadRequestError and correctly failed. Provider JSON errors motivated strict structured output and a larger low-effort completion budget. Multiple debugging requests can affect quota availability. Do not treat the earlier failures as passing evidence or assume their causes were all eliminated permanently.

The owner's local test run hit PermissionError in pytest's shared Windows temp folder before one test executed. That test now uses an isolated, automatically cleaned workspace temporary directory. All 26 local tests subsequently passed. Evaluation progress now displays the safe exception class for failed cases.

## CI/CD status

A new single GitHub Actions workflow runs tests, then live evaluation, then an explicitly requested main-branch deployment only on success. No existing workflow was present to extend. Missing credentials and evaluator crashes fail closed. The workflow has not run in GitHub, and deployment was not tested. Configure GROQ_API_KEY, AWS_DEPLOY_ROLE_ARN, repository-restricted AWS OIDC trust, production required reviewers and branch protection before use. YAML job dependencies and deterministic gate exit codes were reviewed/tested locally; no hosted workflow result is claimed.

## Terraform and AWS status

Read-only plan failed: no valid AWS credential sources. Local state shows only the older TCP 8000 /32 ingress. The reported manual rule is not in that saved state; current drift is unverified. See INFRA_REVIEW.md. A /32 input validation was added locally. No apply, destroy, rule deletion, cloud mutation or deployment was performed.

Historical observations supplied by the owner, not rerun: a 437.02 ms successful remote tool call; three failures triggering the threshold-three CloudWatch alarm; SNS email receipt. These are not new live availability evidence.

## Files changed

- evaluation/evaluator.py: strict parsing/output, account model check, bounded SDK calls, fresh reports, fixed threshold floor and fail-closed gate.
- tests/test_evaluation.py and tests/test_mcp_catalog.py: deterministic gate tests and safe local MCP integration.
- .github/workflows/release.yml: tests/evaluation dependencies and manual gated ECS release.
- client/mcp_client.py: active-interpreter subprocess.
- infra/ecs.tf: narrow ingress input validation.
- pyproject.toml and uv.lock: dotenv dependency consistency and safe pytest discovery.
- .env.example and .gitignore: documented variable names and ignored generated evidence.
- README.md, docs/INFRA_REVIEW.md, docs/INTERVIEW_PREP.md and this report: implementation, security review, interview preparation and measured evidence.

## Final manual verification (PowerShell)

```powershell
Set-Location C:\github-mcp-server
.\.venv\Scripts\Activate.ps1
python -m pytest -q -p no:cacheprovider
python -m pip check
python -m compileall -q app client evaluation tests
Remove-Item Env:MCP_SERVER_URL -ErrorAction SilentlyContinue
$env:GITHUB_MCP_READ_ONLY='false'
$env:MCP_TRANSPORT='stdio'
python -m evaluation.evaluator
# Inspect $LASTEXITCODE immediately; 0 is required to release.
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
# After obtaining AWS credentials, this is read-only:
terraform -chdir=infra plan -input=false -no-color -detailed-exitcode
git diff --check
git status --short
```

The owner subsequently authorized committing and pushing the reviewed changes. The project is suitable for an honest interview walkthrough with its limitations and failed-gate behavior explained. It is not a verified production release: hosted CI configuration/run, authenticated AWS drift review and a separately approved deployment remain outstanding. A clean local live evaluation has passed at 98%.
