# Final deployment setup - administrator review required

The application, tests, hosted 98% live evaluation, gated workflow and approved ingress correction are verified. This package prepares the remaining OIDC deployment access; it does not provision it or claim a completed release.

## Current blockers

- AWS explicitly denied iam:ListOpenIDConnectProviders under an organization Service Control Policy. Do not bypass or broadly disable that control. An authorized organization/account administrator must confirm permitted OIDC setup and supply an approved provisioning identity or perform setup.
- The GitHub-related roles visible in the account are the ECS task and execution roles, neither intended for CI deployment. A differently named deployment role could exist; its existence/trust has not been established.
- The current GitHub token receives HTTP 403 when reading Actions secrets/variables. Production environment lookup returned HTTP 404 with that access. Use repository-owner/admin access to configure and verify those settings.

## Concrete configuration prepared for review

1. An administrator checks for the existing GitHub OIDC provider in AWS account 258063471541, reusing it if present. Expected issuer: https://token.actions.githubusercontent.com, audience: sts.amazonaws.com. Create it only if absent and permitted by organization policy.
2. Create or review role github-mcp-server-github-actions using trust-policy.json and permissions-policy.json. Do not reuse the ECS execution/task roles. The trust is limited to this repository's production environment and assumes GitHub's default subject format; verify any custom subject configuration before use.
3. In GitHub Settings > Environments, configure production. Restrict deployment branches to main and configure required reviewers. Confirm those protection features are available for the repository plan and visibility before claiming they are enforced. This environment restriction matters because the OIDC environment subject itself does not include a branch.
4. In Settings > Secrets and variables > Actions > Variables, set AWS_DEPLOY_ROLE_ARN to arn:aws:iam::258063471541:role/github-mcp-server-github-actions (or the actual approved role ARN). GROQ_API_KEY is already available and verified by the successful hosted evaluation.
5. Configure branch protection/rulesets for main requiring the tests and evaluation checks, reviewing the effect on direct pushes. Verify the exact check names from the repository's successful run.

The permission policy grants ECR authentication, image upload to this project's repository, and update/describe access to this existing ECS service. It does not create infrastructure, register task definitions, read secrets, grant IAM access or permit Terraform apply. It matches the current workflow's force-new-deployment of an existing latest-tag task definition. Policy parsing and review are complete; actual authorization/assumption is not verified.

## Final release - separate explicit approval required

After settings are verified, obtain owner approval for publishing an image and redeploying ECS. Use Actions > Test, evaluate and release > Run workflow on main with deploy selected. Tests and fresh live evaluation must pass first, followed by environment approval. The workflow pushes SHA/latest images and rolls the existing service, which may incur costs and change the task public IP. Wait for service stability and verify /health at the newly discovered endpoint. Do not repeat deliberate error-alarm tests unnecessarily.

Until that run succeeds, describe the quality gate as hosted-verified and automated AWS deployment as prepared but unverified. The already deployed service is healthy; this is a separate release-path verification.

References: [GitHub OIDC on AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [AWS ECR push permissions](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-push-iam.html).
