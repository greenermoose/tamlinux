# nftables host firewall (0.6)

- **Status:** Develop for Tamlinux 0.6.4 packaging; host cutover waits for an
  installed 0.6.x and per-step D156 approval (D204).
- **Owners:** Product helpers and template in `tamlinux`; host subnet values
  stay on the machine (not in public Git).
- **Done when:** A 0.6.x install uses owned `/etc/nftables.conf`, SSH helpers
  manage nftables rules, `PermitRootLogin no` is effective, ufw is removed
  after verified cutover, and LocalSend / Docker networking still work.

## Goal

Replace ufw with one owned nftables policy per host so 0.6 has a single
firewall frontend. Preserve SSH subnet restrictions, mDNS, LocalSend
(53317), Docker’s working iptables backend, and IPv6 policy from
fleet-configuration practice.

## Deliverables

1. Public template:
   [`share/nftables/tamlinux-host.conf.template`](../../share/nftables/tamlinux-host.conf.template)
   with `__TAMLINUX_SSH_SUBNET__` placeholders (never real subnets in Git).
2. `tam-setup-security-sshd` / `tam-remove-security-sshd` open and close SSH
   on nftables when the host policy is active; keep a transitional ufw path
   until ufw is removed on that host.
3. Hardening drop-in always sets `PermitRootLogin no` with the existing
   password-auth restrictions.
4. Cutover runbook steps (local console, Snapper + HM generation, verify
   SSH/LocalSend/Docker, then ufw removal) — executed only with Fred’s word.

## Non-goals

- Remote-only blind firewall replacement.
- Enabling Docker’s experimental native nftables backend.
- Publishing home subnet CIDRs in public repositories.
- Declaring K57/K58 `pass` before physical host proof.

## Cutover order (installed 0.6.x)

1. Local console available; record rollback line.
2. Install rendered `/etc/nftables.conf` from the template; `nft -c -f` then
   enable/start `nftables.service`.
3. Confirm fresh SSH from an allowed host, refuse root SSH, LocalSend, Docker
   DNS/egress.
4. Disable ufw and remove the package only after those checks (separate
   approval).
5. Persist across an approved reboot.
