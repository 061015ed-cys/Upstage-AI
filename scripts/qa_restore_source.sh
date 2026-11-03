#!/usr/bin/env bash
# Explicitly run in an authenticated Git clone of the COPY repository.
# Never writes to the source repository; never force-pushes.
set -euo pipefail

COPY_URL="https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy.git"
SOURCE_URL="https://github.com/dohun3540-crypto/leadtime-guardian-agent.git"
QA_BRANCH="feat/independent-qa-integration"
TARGET_BRANCH="feat/qa-source-restore-20261031"
SOURCE_REF="refs/heads/feat/specs-data-engine-20261029"
BASELINE_SHA="f196c694917f2d9e5f4ec228c752bd3f2a4eb882"

cd "$(git rev-parse --show-toplevel)"
test -z "$(git status --porcelain)" || { echo "ABORT: uncommitted changes"; exit 2; }
test "$(git branch --show-current)" = "$QA_BRANCH" || {
  echo "ABORT: checkout $QA_BRANCH before using this script"; exit 2;
}
git remote get-url origin | grep -Fx "$COPY_URL" >/dev/null || {
  echo "ABORT: origin is not the designated copy repository"; exit 2;
}
if git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
  echo "ABORT: target branch already exists"; exit 2
fi
if git remote | grep -Fx source-readonly >/dev/null; then
  git remote get-url source-readonly | grep -Fx "$SOURCE_URL" >/dev/null || {
    echo "ABORT: source-readonly remote points elsewhere"; exit 2;
  }
else
  git remote add source-readonly "$SOURCE_URL"
fi
# Fetching does not update the source repository.
git fetch --no-tags source-readonly "$SOURCE_REF"
actual_sha="$(git rev-parse FETCH_HEAD)"
echo "Source HEAD: $actual_sha"
echo "Earlier checkpoint: $BASELINE_SHA"
git cat-file -e "$actual_sha^{commit}"
git switch -c "$TARGET_BRANCH"
git merge --no-edit --no-ff --allow-unrelated-histories -m   "chore(qa): restore upstream source tree into isolated QA integration branch" "$actual_sha"

# The source files must match the fetched commit byte-for-byte.
if git diff --name-only "$actual_sha" HEAD | grep -Ev   '^(src/leadtime_guardian/qa/|tests/test_qa_|scripts/qa_|docs/INTEGRATION_GATE\.md$|docs/QA_|\.github/workflows/qa\.yml$)' ; then
  echo "ABORT: unexpected differences against source files; do not push"
  exit 3
fi

echo "Installing declared project test dependencies"
python -m pip install -r requirements-agents.txt
echo "Running full repository checks before pushing"
python -m pytest -q
python -m ruff check .
echo "Checks passed. Pushing isolated restored integration branch."
git push origin "HEAD:refs/heads/$TARGET_BRANCH"
echo "DONE: $TARGET_BRANCH / $(git rev-parse HEAD)"
