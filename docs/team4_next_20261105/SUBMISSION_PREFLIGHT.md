# Submission package preflight

The repository has no designated final submission folder or ZIP. Current outcome is BLOCKED; the synthetic test fixture proved only `PRECHECK_ONLY`. No ZIP was created, approved, uploaded, or submitted.

For a real candidate, prepare a private JSON manifest with `files` entries containing a safe relative `path`, exact `size_bytes`, and lowercase `sha256`. Add a nonempty `required_evidence_references` list of paths in `files`. Run `python -m qa.submission_preflight --candidate PRIVATE_PACKAGE_OR_ZIP --manifest PRIVATE_MANIFEST.json`. The checker rejects missing or extra files, duplicate paths, changed size/SHA, corrupt or unsafe ZIP entries, symlinks, excessive sizes, and unapproved names containing private Native, XLSX, key, secret, token, or credential indicators. Such files require `approved_sensitive_paths` and `public_approval_reference`, which record a claim for manual review but never authorize publication. A clean run says `PRECHECK_ONLY` and exits 2.

The existing `scripts/qa_release_evidence_check.py` separately checks C001 release evidence and Stage identity; it is not a general submission ZIP verifier. Submission content and public permission still require manual review against the actual portal rules before any external action.
