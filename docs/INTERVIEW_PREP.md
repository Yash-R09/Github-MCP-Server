# Interview preparation

## Two-minute project explanation

“My project is a Python GitHub MCP server exposing 21 tools for repositories, files, issues, pull requests, branches, commits, search and labels. It demonstrates the DevOps work around an AI application: controlled tool access, container delivery, infrastructure as code, monitoring and release validation.

An MCP client discovers the server's tool schemas and invokes tools through a standard protocol. The server translates calls into GitHub REST requests. A separate Groq assistant helps select and call tools. The interactive assistant requests confirmation before writes, and the deployed server uses read-only mode.

Docker packages the server, and Terraform describes ECR, ECS Fargate, IAM roles, Secrets Manager and monitoring. The execution role fetches the GitHub token for container startup; the application task role has no AWS permissions. Structured tool events become CloudWatch metrics. The owner reports a historical successful call at 437.02 ms and three failures triggering an alarm and an SNS email.

The evaluation checks tool-name selection on 50 prompts. The release workflow runs tests and live model evaluation, blocking deployment below 90 percent or on any evaluator/API error. Deployment also requires a manual release request. I distinguish deterministic gate tests from real model quality and report failures honestly.

This is an interview demonstration with production-minded controls. Authentication, TLS, stable ingress, immutable image deployment and secure remote Terraform state are areas for improvement.”

Use the latest verification report for the actual live score. Do not claim personal ownership of work or AWS tests you did not perform.

## Complete architecture

1. A client connects through stdio locally or Streamable HTTP remotely and discovers tool names, descriptions and input schemas.
2. The MCP server validates input types and delegates to a dedicated GitHub HTTPX client.
3. That client sends token-authenticated GitHub REST requests and returns results through MCP.
4. Docker packages the server; ECR stores images; ECS Fargate runs the task without managing EC2 hosts.
5. Terraform defines networking, roles, the secret container, service and monitoring. Plan compares configuration with refreshed state; apply is a separate approved operation.
6. The execution role supports startup; the application task role currently grants no AWS API permissions.
7. Structured tool logs produce CloudWatch metrics. Alarms publish to SNS, which delivers confirmed email subscriptions.
8. GitHub Actions runs tests, then live evaluation, then permits an explicitly requested deployment only on success.

## Why MCP?

It provides a common discovery and invocation interface so compatible AI clients can reuse the GitHub capabilities. It does not itself decide whether a user's intent is safe or supply the missing application authentication in this deployment.

## How GitHub communication works

Tool functions pass repository identifiers and arguments to the HTTP client. It adds a GitHub token, sets bounded timeouts and retries transient read failures. Writes are not blindly retried because duplicate effects are possible. Token scopes and repository permissions still control what GitHub permits.

## Why Docker and ECS Fargate?

Docker keeps runtime packaging consistent. Fargate avoids host provisioning and patching for this small demonstration. Networking, IAM, health checks, sizing and cost management remain our responsibility. Kubernetes would add unnecessary complexity here.

## How Terraform manages infrastructure

Configuration declares desired resources, while state maps those declarations to AWS resource IDs. Refresh is needed to detect current drift. A manually added security-group rule may differ from the saved state. We review a plan before approving apply. Local state has security and collaboration limitations; remote encrypted state with locking is a future improvement.

## IAM and Secrets Manager

ECS uses the execution role to pull the image, write logs and read the specific GitHub secret at startup. Application code uses the task role, which currently has no AWS permissions. The secret value is populated outside Terraform to keep it out of state. It remains sensitive inside the running container. The deployed read-only tool catalog further reduces exposure.

## CloudWatch metrics and alarms

Tool events contain tool name, status, duration and exception class, without input arguments. Metric filters count errors and extract latency. The error alarm uses Sum >= 3 over 300 seconds. The latency alarm uses Average > 5000 ms over 300 seconds. Missing data is nonbreaching, so silence does not establish availability. The dashboard visualizes error and latency data.

## How SNS was tested

The owner reports that three deliberately failed remote calls caused ALARM and an SNS email arrived. Label this as historical evidence; AWS was not reverified during current local work. The 437.02 ms observation is one successful call, not a load-test benchmark or percentile. Email subscriptions require confirmation.

## LLM evaluation

The unchanged dataset contains 50 prompts with expected tool names. The evaluator obtains the actual MCP catalog and asks Groq for one JSON selection per prompt. It checks account model availability, exact JSON shape and tool membership. Strict schema output constrains the response to available tool names; it does not supply the expected answer. A fixed seed, temperature zero, low reasoning effort and a bounded completion budget improve consistency, but model behavior can change.

Correct cases divided by all 50 gives the pass rate. At least 45 correct are required, and any API/parsing error independently blocks release. Reports include settings, time, hashes and per-case outcomes. This evaluates routing only, not arguments, permissions, execution results or the full assistant loop. Fixture tests validate logic without claiming model quality. The latest full live run achieved 49/50 correct (98%), one wrong selection and zero API errors, passing the local release gate. Earlier provider-error runs correctly failed. GitHub-hosted tests and live evaluation also passed at commit 453293a, attempt 2, with 98% and zero API errors. Deployment was skipped; no AWS release is claimed. Use docs/VERIFICATION.md for measured results.

## How the 90% gate blocks deployment

The workflow deploy job depends on tests and live evaluation. A nonzero evaluator exit blocks it. Missing secrets, crashes and API failures fail closed. Fixtures never replace live release evidence. Deployment additionally requires main-branch manual dispatch with deployment selected. Configure production environment required reviewers and AWS OIDC before use; those settings are not established by a YAML file alone.

## Challenges and responses

- A prior model-not-found report required checking current provider/account availability instead of assuming the old model was still the problem.
- The earlier gate could tolerate API failures within the wrong-answer budget. Errors now independently veto release.
- Live JSON-generation errors motivated strict structured outputs and a larger completion budget with low reasoning effort. Report actual full-run results, not just a successful diagnostic case.
- Malformed responses now fail strict parser tests rather than causing accidental passes.
- Deployed read-only mode omits write tools, so full evaluation uses local discovery without executing tools.
- Read-only AWS review confirmed the manual security-group rule and both old client IPs. After explicit owner approval, Terraform applied one in-place security-group update to the current workstation /32. Live rules were verified and the post-apply plan was clean.
- The MCP subprocess now uses the active Python interpreter rather than an arbitrary python on PATH.

## Ten likely interview questions

1. **What does MCP add?** Standard discovery and invocation so multiple clients can reuse GitHub tools.
2. **Why not retry every request?** Retrying writes can duplicate issues or commits; reads are safer to retry with bounds.
3. **Execution role versus task role?** ECS uses execution permissions for startup; application code uses task-role permissions.
4. **Why Fargate instead of Kubernetes?** Managed containers suit the small service without additional orchestration administration.
5. **What does Terraform state do?** It links declared resources to real IDs and records known attributes; refresh detects new drift.
6. **How is the gate calculated?** Correct selections / 50 times 100, requiring at least 90% and zero evaluator errors.
7. **What if Groq is unavailable?** Bounded retries/timeouts end in failure; deployment remains blocked.
8. **Does 90% prove safety?** No. It measures routing on a limited dataset; argument correctness, security and execution need separate testing.
9. **How was alerting verified?** Cite the owner's historical three-error test and email receipt, distinguishing it from current local tests.
10. **What would you improve first?** Authenticated TLS ingress, a stable endpoint, immutable image references and rollback, secure remote state and broader evaluation.

## Known limitations and improvements

The demo has no application authentication or TLS, and its public task IP can change. A narrowly scoped security group and read-only server are essential. CLI confirmation does not secure direct MCP calls. AWS drift was verified read-only outside the sandbox; the approved ingress correction was applied and verified with a clean post-apply plan. Model quality is nondeterministic and must be reported from the current run. CI secrets, OIDC trust and environment reviewers require repository setup. Mutable image tags and dependency ranges limit reproducibility. AWS and model requests can incur costs. The quality gate has now passed in GitHub Actions; do not confuse that with an AWS deployment, which remains unverified.
