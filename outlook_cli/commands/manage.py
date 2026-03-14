"""Management commands: mark-read, move, delete."""

from __future__ import annotations

import click

from ._common import _get_client, _handle_api_error, print_success


@click.command("mark-read")
@click.argument("message_ids", nargs=-1, required=True)
@click.option("--unread", is_flag=True, help="Mark as unread instead")
@_handle_api_error
def mark_read(message_ids: tuple, unread: bool):
    """Mark messages as read (or unread with --unread). Accepts multiple IDs."""
    client = _get_client()
    status = "unread" if unread else "read"
    for mid in message_ids:
        client.mark_read(mid, is_read=not unread)
        print_success(f"Message #{mid} marked as {status}")


@click.command()
@click.argument("message_ids", nargs=-1, required=True)
@click.argument("destination")
@_handle_api_error
def move(message_ids: tuple, destination: str):
    """Move messages to another folder. Accepts multiple IDs."""
    client = _get_client()
    for mid in message_ids:
        client.move_message(mid, destination)
        print_success(f"Message #{mid} moved to {destination}")


@click.command()
@click.argument("message_ids", nargs=-1, required=True)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@_handle_api_error
def delete(message_ids: tuple, yes: bool):
    """Delete messages. Accepts multiple IDs."""
    if not yes:
        ids_str = ", ".join(f"#{m}" for m in message_ids)
        click.confirm(f"Delete {ids_str}?", abort=True)
    client = _get_client()
    for mid in message_ids:
        client.delete_message(mid)
        print_success(f"Message #{mid} deleted")
