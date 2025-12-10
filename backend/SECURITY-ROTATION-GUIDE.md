# Security: Credential Rotation Guide

## URGENT: Credentials Were Exposed

The following credentials were previously hardcoded in this repository and **MUST be rotated immediately**:

### 1. Supabase Service Role Key
**Exposed in:** `config.py`, `scripts/optimize_company_registry.py`
**Risk:** Full database access, bypasses RLS

**Rotation steps:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select project: `wzkohritxdrstsmwopco`
3. Settings → API → Service Role Key
4. Click "Generate new key"
5. Update your `.env` file with the new key
6. Restart the application

### 2. Supabase Management API Token
**Exposed in:** `scripts/optimize_company_registry.py`
**Risk:** Access to project settings, database schema

**Rotation steps:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Account → Access Tokens
3. Revoke the old token (starting with `sbp_v0_ab0cd56b...`)
4. Generate a new token
5. Update your `.env` file

### 3. Bolagsverket OAuth2 Credentials
**Exposed in:** `scripts/test_bv_api.py`, `scripts/test_vdm_client.py`, `ARCHITECTURE-PLAN.md`
**Risk:** Unauthorized API access

**Rotation steps:**
1. Contact Bolagsverket to rotate client credentials
2. Or access their developer portal to generate new credentials
3. Update your `.env` file

---

## Git History Cleanup

**IMPORTANT:** The credentials still exist in Git history. To fully remove them:

### Option 1: git filter-repo (Recommended)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Create backup first!
cp -r loop-auto loop-auto-backup

# Remove sensitive files from history
git filter-repo --path config.py --invert-paths --force
git filter-repo --path scripts/test_bv_api.py --invert-paths --force
git filter-repo --path scripts/test_vdm_client.py --invert-paths --force
git filter-repo --path scripts/optimize_company_registry.py --invert-paths --force

# Or remove specific strings
git filter-repo --replace-text <(echo 'CLIENT_SECRET_REDACTED==>REDACTED')
git filter-repo --replace-text <(echo 'CLIENT_ID_REDACTED==>REDACTED')
```

### Option 2: BFG Repo-Cleaner

```bash
# Install BFG
brew install bfg

# Create a file with secrets to remove
cat > secrets.txt << EOF
CLIENT_SECRET_REDACTED
CLIENT_ID_REDACTED
MGMT_TOKEN_REDACTED
SUPABASE_KEY_REDACTED
EOF

# Run BFG
bfg --replace-text secrets.txt

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Option 3: Start Fresh (Simplest)

If the repo is not public and has limited history:

```bash
# Archive old repo
mv .git .git-backup

# Initialize fresh
git init
git add .
git commit -m "Initial commit (cleaned)"

# Push to new remote
git remote add origin <new-repo-url>
git push -u origin main
```

---

## Checklist

- [ ] Rotated Supabase Service Role Key
- [ ] Rotated Supabase Management API Token
- [ ] Contacted Bolagsverket for new OAuth credentials
- [ ] Cleaned Git history (if repo was public)
- [ ] Created `.env` file from `.env.example`
- [ ] Verified application starts with new credentials
- [ ] Deleted `secrets.txt` file (if created for BFG)

---

## Prevention

1. **Never hardcode secrets** - Always use environment variables
2. **Use `.env.example`** - Template without real values
3. **Pre-commit hooks** - Consider adding secret detection:
   ```bash
   pip install detect-secrets
   detect-secrets scan --all-files
   ```
4. **Review PRs** - Check for accidental credential commits

---

*Generated: 2025-12-09*
