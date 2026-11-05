# Infrastructure review - 5 November 2026

## Verified live findings

AWS access is available through the normal Windows account's default profile, outside the restricted execution sandbox. Earlier sandbox-only credential failures did not establish that the workstation lacked credentials. Read-only STS, EC2, ECS and Terraform calls succeeded. The owner subsequently approved the single security-group ingress correction; its application and verification are recorded below.

Before correction, security group sg-029f078879d80e52d permitted TCP 8000 from:

| Rule ID | CIDR | Finding |
|---|---|---|
| sgr-0ee0b181e31a9b29c | 49.43.24.33/32 | Older Terraform-managed address |
| sgr-0e771c128663aa13c | 49.43.26.146/32 | Confirmed manually added rule, absent from original saved state |

Outbound all-protocol IPv4 access remains configured. The current observed workstation outbound IPv4 is 49.43.24.52. Both former inbound addresses differed from it; public IPs can change, so recheck before apply or a demo.

ECS service github-mcp-server in github-mcp-server-cluster is ACTIVE, desired=1, running=1, pending=0, rollout COMPLETED. This verifies service/task status, not current remote MCP invocation or the historical alarm pipeline. The task's public IP can change on replacement.

## Approved correction - applied and verified

The ignored local terraform.tfvars allowed_cidr value is prepared as 49.43.24.52/32. The final refreshed read-only Terraform plan reports **0 to add, 1 to change, 0 to destroy**, exit 2 (changes present, not a command failure). The only proposed resource action is an in-place update to aws_security_group.app: replace both older TCP 8000 /32 ingress entries with the current workstation /32. No ECS task, deployment, IAM, SNS or CloudWatch resource changes remain in that plan.

The initial plan also proposed changing the latency metric filter's empty default to zero and rewriting its pattern from `{ $.event = tool_call }` to the quoted equivalent. Local observability.tf now explicitly preserves the live empty default and exact pattern. A subsequent refreshed plan confirmed no monitoring update is proposed. Terraform fmt -check and validate pass. Temporary plan files were removed after inspection.

The owner explicitly approved this plan. Immediately before apply, the outbound IPv4 was rechecked as 49.43.24.52 and the fresh saved plan was programmatically restricted to a single in-place ingress update on the expected security group. Terraform apply exited 0: **0 added, 1 changed, 0 destroyed**.

Post-apply EC2 verification confirms the sole inbound rule is TCP 8000 from 49.43.24.52/32, rule ID sgr-01b6fc420ae89eae3. Both old ingress entries were removed. Outbound rules are unchanged. ECS remains ACTIVE with desired=1, running=1, pending=0 and rollout COMPLETED. A refreshed post-apply Terraform plan exited 0 with **No changes. Your infrastructure matches the configuration.** Temporary saved plan files were removed.

No ECS redeployment, resource destruction or monitoring update was performed. Future client public IP changes require another reviewed and approved ingress correction. Inline ingress remains authoritative; do not add separate Terraform rule resources for the same ingress.

## Remaining work

GitHub-hosted tests and live evaluation pass, but AWS deployment OIDC role, production reviewers and branch protection still need verification. Local state remains ignored; use secure backups and consider encrypted remote state with locking as a separate approved infrastructure change. Existing ECR force-delete and immediate secret deletion settings deserve review before teardown. Only the approved Terraform security-group update was applied. No destroy, application deployment or unrelated cloud mutation occurred.
