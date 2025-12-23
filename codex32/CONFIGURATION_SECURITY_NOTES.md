# Configuration Wizard - Security & Validation Improvements

**Date:** December 2025  
**Status:** Fixed & Hardened  

---

## Issues Fixed

### 1. **Command Injection Prevention (APP_NAME & APP_VERSION)**

**Problem:**
Users could accidentally (or maliciously) enter shell commands:
```
Application name [Codex-32]: make run # Start system
Application version [1.0.0]: make new-bot # Create bot
```

This would save:
```
APP_NAME=make run # Start system
APP_VERSION=make new-bot # Create bot
```

**Solution:**
Added `validate_app_name()` and `validate_version()`:
- Rejects command-like strings: `make`, `sudo`, `#`, `;`, `&&`, etc.
- Validates semantic versioning: `X.Y.Z` format
- Clear error messages guide users

```python
def validate_app_name(self, name: str) -> Tuple[bool, str]:
    forbidden = ['make', 'sudo', '&&', '||', ';', '|', '#', '`', '$']
    for char in forbidden:
        if char in name:
            return False, f"Cannot contain '{char}'"
    return True, ""
```

---

### 2. **Weak Secret Key Rejection**

**Problem:**
Accepting weak or short secrets like `1234`:
```
JWT secret key: 1234
```

Results in:
```
SECRET_KEY=1234  # Vulnerable to brute-force!
```

**Solution:**
Added `validate_secret_key()`:
- Enforces minimum 32 characters
- Warns users about weak keys
- Auto-generates secure keys if users press Enter

```python
# Weak key rejected
JWT secret key: 1234
❌ Error: Secret key must be at least 32 characters

# Empty input auto-generates secure key
JWT secret key: [press Enter]
✓ Auto-generated secure secret
```

---

### 3. **Database Password Validation**

**Problem:**
- Accepted weak passwords
- No strength validation
- Showed "no password" as valid without warning

**Solution:**
Added `validate_password_strength()`:
- Minimum 8 characters
- Must contain letters + (digits or special chars)
- Warns if no password set (for production)
- Allows empty for dev SQLite (fine), but warns for PostgreSQL/MySQL

```python
# Weak password rejected
PostgreSQL password: 123
❌ Error: Password should contain letters and numbers/special chars

# Strong password accepted
PostgreSQL password: MySecure@Pass123
✓ Valid

# No password warning
PostgreSQL password: [press Enter]
⚠️  Warning: No password set. Not recommended for production.
Continue without password? [yes/no]: 
```

---

### 4. **Secret Masking in Review**

**Problem:**
Secrets were visible in configuration review:
```
DATABASE_URL = postgresql://postgres:MyPassword@localhost:5432/codex32
SECRET_KEY = my-very-long-secret-key-value-here
```

**Solution:**
Mask all sensitive fields in review display:
- PASSWORD, SECRET, TOKEN, KEY fields show `[HIDDEN]`
- DATABASE_URL with credentials shows `[HIDDEN - contains credentials]`
- Secrets never echo to console during review

```
DATABASE_URL                       = [HIDDEN - contains credentials]
SECRET_KEY                         = [HIDDEN]
```

---

## Validation Functions Added

```python
validate_app_name(name)           # Rejects command-like strings
validate_version(version)         # Enforces X.Y.Z format
validate_password_strength(pwd)   # Minimum 8 chars, complexity
validate_secret_key(key)          # Minimum 32 characters
validate_port(port)               # 1024-65535 (existing, still good)
validate_db_url(url)              # Valid DB scheme (existing, still good)
validate_log_level(level)         # Valid log levels (existing, still good)
```

---

## Input Handling Improvements

### APP_NAME & APP_VERSION
```bash
# Before: Could accept "make run"
# After: Only accepts valid app names
❌ Application name cannot contain 'make'
❌ Version should be in format: X.Y or X.Y.Z
```

### Database Passwords
```bash
# Before: Weak passwords accepted
# After: Strength validation required
PostgreSQL password: weak123
❌ Error: Password should contain letters and numbers/special chars

PostgreSQL password: MySecure@Pass123
✓ Valid
```

### JWT Secret
```bash
# Before: Could be "1234"
# After: Auto-generate or enforce minimum
JWT secret key: [leave empty to auto-generate, min 32 chars]
[press Enter] → Auto-generates 32-char secure key
```

---

## Review Display

**Before:**
```
DATABASE_URL                       = postgresql://postgres:password@localhost:5432/codex32
SECRET_KEY                         = my-secret-key-value
```

**After:**
```
DATABASE_URL                       = [HIDDEN - contains credentials]
SECRET_KEY                         = [HIDDEN]
LOG_LEVEL                          = INFO
```

---

## Port Validation Enhancement

**Example - Port input handling:**
```
API port [8000]: 001
❌ Error: Port must be between 1024 and 65535

API port [8000]: 10001
✓ Valid

API port [8000]: notaport
❌ Error: Port must be a valid number
```

---

## Complete Validation Flow

```
User Input → Validator Function → Result
                     ↓
            ✓ Valid → Store & Continue
            ❌ Invalid → Show Error & Retry
                     ↓
            User Re-enters
```

**Example:**
```
PostgreSQL password: weak
❌ Error: Password should contain letters and numbers/special chars
PostgreSQL password: Strong@Pwd123
✓ Valid
```

---

## Security Best Practices Now Enforced

1. ✅ **No command injection** - APP_NAME/VERSION validated
2. ✅ **Strong secrets** - Minimum 32 chars, auto-generated if empty
3. ✅ **Strong passwords** - Minimum 8 chars, complexity required
4. ✅ **Secret masking** - Never shown in review or logs
5. ✅ **Valid configuration** - All inputs validated before saving
6. ✅ **Clear errors** - Users understand what went wrong

---

## Usage Examples

### Successful Configuration
```bash
$ make configure

Application name: MyBotOrchestrator
Application version: 1.0.0
[API host: 127.0.0.1]
[API port: 8000]
[PostgreSQL setup...]
PostgreSQL password: MySecure@Pwd123
✓ Valid
[... continue ...]

CONFIGURATION REVIEW
APP_NAME                           = MyBotOrchestrator
APP_VERSION                        = 1.0.0
DATABASE_URL                       = [HIDDEN - contains credentials]
SECRET_KEY                         = [HIDDEN]

Is this configuration correct? [yes]: yes
✓ Configuration saved to .env
```

### Handling Invalid Input
```bash
$ make configure

Application name: make run
❌ Error: Application name cannot contain 'make'

Application name: MyApp
✓ Valid

Application version: 1
❌ Error: Version should be in format: X.Y or X.Y.Z

Application version: 1.0.0
✓ Valid
```

---

## What Users Need to Know

1. **APP_NAME**: Your app name (e.g., "Codex-32", "MyOrchestrator")
   - ✅ "Codex-32", "My Bot Manager", "OrderProcessor"
   - ❌ "make run", "sudo ./app", "$(rm -rf /)"

2. **APP_VERSION**: Semantic version (e.g., "1.0.0", "0.1.0")
   - ✅ "1.0.0", "0.1.0", "2.5"
   - ❌ "latest", "dev", "make new-bot"

3. **JWT SECRET**: Confidential key for signing tokens
   - ✅ Leave empty → auto-generated (recommended)
   - ✅ Enter 32+ character string with complexity
   - ❌ "secret", "password123", "1234"

4. **DATABASE PASSWORD**: For PostgreSQL/MySQL
   - ✅ Strong passwords enforced
   - ✅ Empty accepted for SQLite (safe)
   - ⚠️ Empty rejected with warning for PostgreSQL/MySQL

---

## Testing the Configuration Wizard

```bash
# Run the wizard
make configure

# Verify .env created correctly
cat .env

# Start the system
make run
```

---

## Error Messages Users Will See

| Input | Error | Solution |
|-------|-------|----------|
| APP_NAME: "make run" | Cannot contain 'make' | Use proper app name |
| VERSION: "1" | Should be X.Y or X.Y.Z | Use "1.0.0" format |
| PORT: "abc" | Must be a valid number | Enter valid port |
| PORT: "999" | Between 1024 and 65535 | Use valid port range |
| PASSWORD: "weak" | Needs letters and numbers | Use "SecurePass123" |
| SECRET: "short" | At least 32 characters | Leave empty or use long key |

---

## Summary

The configuration wizard is now **hardened against common mistakes** while remaining **user-friendly**:

✅ Prevents accidental command injection  
✅ Enforces strong secrets and passwords  
✅ Masks sensitive data in review  
✅ Clear error messages guide users  
✅ Auto-generates secure defaults  
✅ Validates all inputs before saving  

**Result:** Fewer security issues, better user experience, production-ready configuration.

---

**Version:** 1.0  
**Status:** Complete & Tested  
**Date:** December 2025
