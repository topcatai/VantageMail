# -*- coding: utf-8 -*-
from typing import Dict, List
from utils.logger import log_info, log_error, log_realtime_count

def sync_folder_messages(provider, db, account_email: str, folder_id: str, limit: int = None, progress_callback=None) -> List[Dict]:
    """Synchronize remote IMAP messages with SQLite database cached messages.

    1. Fetch remote messages in chunks of 100.
    2. Retrieve cached messages.
    3. Update SQLite cache dynamically.
    4. Return the refreshed cache list.
    """
    log_info(f"Sync started for folder '{folder_id}' on account '{account_email}'.")
    
    # Get cache
    cached_msgs = db.get_cached_emails(account_email, folder_id)
    cached_dict = {str(c['id']): c for c in cached_msgs}
    
    all_remote_msgs = []
    new_emails_count = [0]

    def uid_callback(remote_uids):
        # Delete cache entries that are no longer on the server
        remote_uid_strs = {str(uid) for uid in remote_uids}
        for cid in list(cached_dict.keys()):
            if cid not in remote_uid_strs:
                db.delete_cached_email(account_email, folder_id, cid)
                del cached_dict[cid]

    def chunk_callback(chunk_msgs):
        to_save = []
        for rmsg in chunk_msgs:
            rid = str(rmsg['id'])
            all_remote_msgs.append(rmsg)
            
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
                cached_dict[rid] = rmsg
            else:
                # Insert new message
                to_save.append(rmsg)
                new_emails_count[0] += 1
                cached_dict[rid] = rmsg
                
        if to_save:
            db.batch_save_emails(account_email, folder_id, to_save)
            
        if progress_callback:
            # Use sorted in-memory cache state to avoid redundant SQLite queries
            current_cached = sorted(
                cached_dict.values(),
                key=lambda m: m.get('date') or '',
                reverse=True
            )
            try:
                progress_callback(current_cached)
            except Exception as cb_err:
                log_error(f"Error executing progress_callback in sync_folder_messages: {cb_err}")

    try:
        # Pass chunk_callback and uid_callback to fetch_messages
        remote_msgs = provider.fetch_messages(
            folder_id, 
            limit=limit, 
            chunk_callback=chunk_callback, 
            uid_callback=uid_callback
        )
        # Fallback for providers/mocks that return messages directly without invoking callbacks
        if remote_msgs and not all_remote_msgs:
            remote_uids = [m['id'] for m in remote_msgs]
            uid_callback(remote_uids)
            chunk_callback(remote_msgs)
    except Exception as e:
        log_error(f"Sync error fetching remote messages for folder '{folder_id}': {e}", exc_info=True)
        # Return what we currently have in cache rather than crashing
        return db.get_cached_emails(account_email, folder_id)

    log_info(f"Sync completed for folder '{folder_id}' on account '{account_email}': received {new_emails_count[0]} new emails.")
    log_realtime_count(db)
    return db.get_cached_emails(account_email, folder_id)

