"""
Script to identify and remove spam/bot accounts from the database

Usage:
    python -m scripts.cleanup_spam_accounts [--dry-run] [--delete]
"""

import sys
import os
import re
from datetime import datetime, timedelta, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy import and_


def is_spam_account(user: User) -> tuple[bool, list[str]]:
    """
    Identify if a user account is likely spam.
    
    Returns:
        (is_spam, reasons) - tuple of boolean and list of reason strings
    """
    reasons = []
    
    # Check for URLs/links in full_name
    if re.search(r'(https?://|bit\.ly|tinyurl|ftp://|www\.)', user.full_name, re.IGNORECASE):
        reasons.append(f"Contains URL in full_name: {user.full_name[:50]}")
    
    # Check for emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "]+"
    )
    if emoji_pattern.search(user.full_name):
        reasons.append(f"Contains emojis in full_name: {user.full_name[:50]}")
    
    # Check for promotional/marketing patterns
    if re.search(r'(bonus|free|click|tikla|guvenli)', user.full_name, re.IGNORECASE):
        reasons.append(f"Contains promotional text: {user.full_name[:50]}")
    
    # Check for non-name characters pattern (too many special chars)
    if not re.match(r"^[a-zA-Z\s\-']+$", user.full_name):
        reasons.append(f"Contains invalid characters in full_name: {user.full_name[:50]}")
    
    # Check for unverified accounts created in bulk (multiple in short timespan)
    if not user.is_verified:
        # This is a secondary indicator
        pass
    
    return len(reasons) > 0, reasons


def cleanup_spam_accounts(dry_run: bool = True, delete: bool = False):
    """
    Identify and optionally delete spam accounts.
    
    Args:
        dry_run: If True, only report without deleting (default: True)
        delete: If True, actually delete identified spam accounts
    """
    db = SessionLocal()
    
    try:
        # Query all users
        users = db.query(User).all()
        
        spam_accounts = []
        legitimate_accounts = []
        
        print(f"\n📊 Scanning {len(users)} user accounts for spam...\n")
        
        for user in users:
            is_spam, reasons = is_spam_account(user)
            
            if is_spam:
                spam_accounts.append((user, reasons))
                print(f"🚨 SPAM DETECTED - User ID {user.id}:")
                print(f"   Email: {user.email}")
                print(f"   Name: {user.full_name}")
                print(f"   Created: {user.created_at}")
                print(f"   Reasons:")
                for reason in reasons:
                    print(f"     - {reason}")
                print()
            else:
                legitimate_accounts.append(user)
        
        # Summary
        print("\n" + "="*60)
        print(f"✅ Legitimate accounts: {len(legitimate_accounts)}")
        print(f"🚨 Spam accounts found: {len(spam_accounts)}")
        print("="*60 + "\n")
        
        if spam_accounts and delete and not dry_run:
            print("⚠️  DELETING SPAM ACCOUNTS...")
            for user, reasons in spam_accounts:
                try:
                    db.delete(user)
                    print(f"   ✓ Deleted user {user.id} ({user.email})")
                except Exception as e:
                    print(f"   ✗ Failed to delete user {user.id}: {e}")
            
            db.commit()
            print(f"\n✅ Successfully deleted {len(spam_accounts)} spam accounts\n")
        
        elif dry_run:
            print("📋 DRY RUN MODE - No accounts were deleted")
            print("To actually delete, run with: --delete\n")
        
        return spam_accounts
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up spam/bot accounts")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete identified spam accounts (default: dry-run only)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report without deleting (default behavior)"
    )
    
    args = parser.parse_args()
    
    dry_run = not args.delete or args.dry_run
    cleanup_spam_accounts(dry_run=dry_run, delete=args.delete)
