# Verification report - 5 November 2026

## Current local checks

- 27 pytest tests passed, including the existing GitHub retry tests, evaluator fixture/boundary/error/CLI tests and real local stdio MCP catalog tests for all 21 tools and the 16-tool read-only catalog, with dotenv loading disabled.
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

The [GitHub Actions run at commit 453293a, attempt 2](https://github.com/Yash-R09/Github-MCP-Server/actions/runs/42036515092) completed successfully. Hosted tests passed; live evaluation measured 49/50 correct (98%), one wrong-tool answer and zero errors, with passed=true. The provider model was openai/gpt-oss-20b and the report timestamp was 2026-11-05T13:40:24.419429+00:00 (19:10:24 IST). The deploy job was skipped as expected for a push-triggered run. This verifies hosted tests and live quality gating, not deployment.

The first hosted run failed because the MCP subprocess did not receive application environment variables. Explicit forwarding of required server settings fixed this; regression tests disable dotenv and exercise both full and read-only catalogs. The next hosted attempt passed tests but failed closed because GROQ_API_KEY was empty. After the owner added the repository Actions secret and reran the failed job, evaluation passed. These failures demonstrate that neither test failure nor missing credentials bypasses the gate.

The workflow runs tests, live evaluation and then an explicitly requested main-branch deployment only on success. Repository GROQ_API_KEY availability is now verified by successful hosted execution. AWS_DEPLOY_ROLE_ARN, repository-restricted AWS OIDC trust, production required reviewers and branch protection still require verification before deployment. The local token received HTTP 403 when inspecting repository secrets/variables, and production environment lookup returned HTTP 404 with that access. AWS access was subsequently verified outside the sandbox through the default profile; see the infrastructure review below. No repository settings were changed by the agent. The separately approved AWS ingress update is recorded below; no application deployment occurred.

## Terraform and AWS status

Read-only AWS calls and refreshed Terraform plans now succeed outside the sandbox using the normal Windows default profile. The earlier sandbox credential errors were an execution-context limitation. Live EC2 confirms both older TCP 8000 /32 rules, including the manually added sgr-0e771c128663aa13c. ECS is ACTIVE with one desired/running task, zero pending tasks and rollout COMPLETED. These checks do not repeat remote tool or alert tests.

The current observed workstation outbound address is 49.43.24.52. Ignored local terraform.tfvars is prepared with allowed_cidr=49.43.24.52/32. The reviewed plan reported 0 additions, 1 in-place change and 0 resource deletions: replace both old ingress entries with the current workstation /32. Local observability.tf matches the exact live latency-filter pattern and empty default, removing the initial unrelated monitoring update. Terraform formatting/validation pass. After explicit owner approval and a fresh IP/plan check, Terraform apply succeeded: 0 added, 1 changed, 0 destroyed. Live EC2 confirms only TCP 8000 from 49.43.24.52/32 (sgr-01b6fc420ae89eae3); both old rules are gone. ECS remains ACTIVE with one running task and rollout COMPLETED. The post-apply plan exited 0 with no changes. No destroy or application deployment was performed. See INFRA_REVIEW.md for rule IDs and access impact.

Historical observations supplied by the owner, not rerun: a 437.02 ms successful remote tool call; three failures triggering the threshold-three CloudWatch alarm; SNS email receipt. These are not new remote tool/alert verification.

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

The owner subsequently authorized committing and pushing the reviewed changes. The project is suitable for an honest interview walkthrough with its limitations and failed-gate behavior explained. It is not a verified production release: AWS deployment-role/environment configuration, a separately approved application deployment remain outstanding. The reviewed ingress correction was approved, applied and verified with a clean post-apply plan. Authenticated read-only AWS drift review is complete. Hosted tests and live evaluation now pass. A clean local live evaluation has passed at 98%.

## Final release preparation

A later read-only IAM check was explicitly denied for iam:ListOpenIDConnectProviders by an AWS organization Service Control Policy. Listed GitHub-named roles were only the ECS task/execution roles; no CI role was verified. No attempt was made to bypass the policy or provision IAM resources. Reviewed candidate trust/permissions JSON and exact remaining setup are in deployment/SETUP.md. Both JSON files parse; all 27 local tests and Terraform fmt/validate pass. These templates have not been applied or authorization-tested. GitHub admin configuration, final change publication and an explicitly approved AWS release remain pending.
