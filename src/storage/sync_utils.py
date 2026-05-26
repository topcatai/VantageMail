# -*- coding: utf-8 -*-
from typing import Dict, List
from utils.logger import log_info, log_error, log_realtime_count

def sync_folder_messages(provider, db, account_email: str, folder_id: str, limit: int = None) -> List[Dict]:
    """Synchronize remote IMAP messages with SQLite database cached messages.

    1. Fetch remote messages.
    2. Retrieve cached messages.
    3. Update SQLite cache:
       - Delete old messages no longer on the server.
       - Insert new messages.
       - Update existing messages if metadata changed (e.g. read status), preserving body.
       - Log sync events, errors, received emails count, and realtime count.
    4. Return the refreshed cache list.
    """
    log_info(f"Sync started for folder '{folder_id}' on account '{account_email}'.")
    try:
        remote_msgs = provider.fetch_messages(folder_id, limit=limit)
    except Exception as e:
        log_error(f"Sync error fetching remote messages for folder '{folder_id}': {e}", exc_info=True)
        # Return what we currently have in cache rather than crashing
        return db.get_cached_emails(account_email, folder_id)

    remote_dict = {str(m['id']): m for m in remote_msgs}
    
    # Get cache
    cached_msgs = db.get_cached_emails(account_email, folder_id)
    cached_dict = {str(c['id']): c for c in cached_msgs}
    
    # 1. Delete cache entries that are no longer on the server
    for cid in list(cached_dict.keys()):
        if cid not in remote_dict:
            db.delete_cached_email(account_email, folder_id, cid)
            del cached_dict[cid]
            
    # 2. Add or update remote messages
    new_emails_count = 0
    to_save = []
    for rid, rmsg in remote_dict.items():
        if rid in cached_dict:
            # Preserve existing body and attachments if cached
            body = cached_dict[rid].get('body')
            if body:
                rmsg['body'] = body
            attachments = cached_dict[rid].get('attachments')
            if attachments:
                rmsg['attachments'] = attachments

            # Save if changed
            if (cached_dict[rid].get('is_read') != rmsg['is_read'] or 
                cached_dict[rid].get('subject') != rmsg['subject'] or 
                cached_dict[rid].get('body') != rmsg.get('body') or 
                cached_dict[rid].get('attachments') != rmsg.get('attachments') or
                cached_dict[rid].get('has_attachment') != rmsg.get('has_attachment') or
                cached_dict[rid].get('sender') != rmsg['sender'] or 
                cached_dict[rid].get('date') != rmsg['date']):
                to_save.append(rmsg)
        else:
            # Insert new message
            to_save.append(rmsg)
            new_emails_count += 1
            
    if to_save:
        db.batch_save_emails(account_email, folder_id, to_save)
            
    log_info(f"Sync completed for folder '{folder_id}' on account '{account_email}': received {new_emails_count} new emails.")
    log_realtime_count(db)
    return db.get_cached_emails(account_email, folder_id)

