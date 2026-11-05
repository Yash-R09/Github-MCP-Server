# Infrastructure review — 5 November 2026

Terraform fmt -check and validate pass. A read-only plan was attempted but failed because no valid AWS credential source was available. Live rule drift and running task availability remain unverified.

The local state records `aws_security_group.app` as `sg-029f078879d80e52d`, with TCP 8000 ingress from `49.43.24.33/32`. Configuration uses one inline ingress rule populated by `allowed_cidr`. The owner reports a manually added rule `sgr-0e771c128663aa13c` for `49.43.26.146/32`; that rule is absent from the saved state inspected here. Neither address is assumed current. Local state is a snapshot, not live AWS evidence.

Smallest proposed correction: identify the trusted demo client's current public IPv4 address, set `allowed_cidr` to that address /32, obtain a refreshed read-only plan, and review removal of both obsolete/unmanaged entries before approving apply. Inline rules are authoritative; a refreshed plan can propose removing out-of-band rules. Do not mix inline and standalone Terraform rule resources. A /32 validation was added locally; it does not mutate AWS.

No apply, destroy, manual rule removal, task replacement or AWS mutation was executed. Changing rules can immediately interrupt access from old IPs; get explicit approval after reviewing the concrete plan. Any task-definition change/redeployment can replace the task and change its public IP. Do not promise a fixed endpoint.

Before a future release, configure the OIDC deployment role and GitHub production environment reviewers. Credentials were unavailable for live infrastructure review. Local state and tfvars are ignored; maintain secure backups and consider encrypted remote state with locking in a later approved infrastructure change. Existing ECR force-delete and immediate secret deletion settings deserve review before any teardown.
