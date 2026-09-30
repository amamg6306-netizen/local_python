#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[2]
fail=[]; passes=[]
def ck(cond,msg): (passes if cond else fail).append(msg)
edit=(ROOT/'admin/payment-method-edit.php').read_text()
listing=(ROOT/'admin/payment-methods.php').read_text()
func=(ROOT/'includes/functions.php').read_text()
auth=(ROOT/'includes/auth.php').read_text()
mig=(ROOT/'database/production/20260924_002_payment_methods.sql').read_text()
env=(ROOT/'.env.example').read_text()
nav=(ROOT/'admin/_nav.php').read_text()

ck('require_admin_mfa_for_sensitive()' in edit,'payment-method changes require admin MFA')
ck('require_recent_admin_reauth(' in edit,'payment-method changes require recent password re-authentication')
ck('verify_csrf()' in edit and 'csrf_field()' in edit,'payment-method form has CSRF protection')
ck("['gateway','upi','bank_transfer']" in edit,'server-side method type allowlist exists')
ck("['provider','business','both']" in edit,'server-side audience allowlist exists')
ck('supported_payment_gateways()' in edit and 'validated_http_url' not in edit,'gateway is allowlisted and no arbitrary redirect URL field is accepted')
for forbidden in ['name="card','name="cvv','name="cvc','name="gateway_secret','name="api_key','name="webhook_secret']:
    ck(forbidden.lower() not in edit.lower(),f'admin form does not request {forbidden[6:]}')
ck('PAYMENT_RAZORPAY_KEY_SECRET' in env and 'REPLACE_WITH_SANDBOX_KEY_SECRET' in env,'gateway secret placeholder documented in environment template')
ck("$indicators[$name] = $present ? 'configured' : 'missing'" in func,'gateway UI receives masked configured/missing indicators only')
ck("WHERE is_active=1" in func and "audience IN (?, 'both')" in func,'new checkout helper returns only active role-appropriate methods')
ck('UPDATE payments' not in edit and 'INSERT INTO payments' not in edit,'admin method changes never mark or create payments')
ck('payment_method_audit' in mig and 'payment_methods' in mig,'versioned migration creates method and audit tables')
ck('payment_method_code_snapshot' in mig and 'payment_method_type_snapshot' in mig,'payments retain immutable method snapshot fields for later checkout')
ck('DROP TABLE' not in mig.upper(),'forward migration does not drop application tables')
ck('Payment Methods' in nav,'admin navigation exposes payment-method management')
ck('Gateway secrets are never displayed or edited here' in listing,'admin listing states secret handling boundary')
print(f'PASS checks: {len(passes)}')
for x in passes: print('  PASS:',x)
print(f'FAIL checks: {len(fail)}')
for x in fail: print('  FAIL:',x)
sys.exit(1 if fail else 0)
