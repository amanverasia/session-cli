"""
Interactive REPL mode for Session CLI.

Provides a persistent session with database and lazy CDP connection.
"""

import cmd
import json
import shlex
import sys
from typing import Optional

try:
    from .config import SessionConfig
    from .database import SessionDatabase
    from .cdp import SessionCDP
    from .user_config import UserConfig
    from .exceptions import CDPError, SessionError
except ImportError:
    from config import SessionConfig
    from database import SessionDatabase
    from cdp import SessionCDP
    from user_config import UserConfig
    from exceptions import CDPError, SessionError


class SessionREPL(cmd.Cmd):
    """
    Interactive REPL for Session CLI.

    Maintains persistent database connection and lazy CDP connection.
    """

    intro = "Session CLI Interactive Mode. Type 'help' for commands, 'quit' to exit.\n"
    prompt = "session> "

    def __init__(
        self,
        profile: Optional[str] = None,
        port: int = 9222,
        json_output: bool = False,
        user_config: Optional[UserConfig] = None,
    ):
        super().__init__()
        self.profile = profile
        self.port = port
        self.json_output = json_output
        self.user_config = user_config or UserConfig()

        # Apply user config defaults if not overridden
        if profile is None:
            self.profile = self.user_config.profile
        if port == 9222 and self.user_config.port != 9222:
            self.port = self.user_config.port
        if not json_output and self.user_config.json_output:
            self.json_output = self.user_config.json_output

        # Lazy connections
        self._db: Optional[SessionDatabase] = None
        self._cdp: Optional[SessionCDP] = None
        self._config: Optional[SessionConfig] = None

        # Cache for tab completion
        self._conversation_cache: list = []

    @property
    def config(self) -> SessionConfig:
        """Get or create SessionConfig."""
        if self._config is None:
            self._config = SessionConfig(profile=self.profile)
        return self._config

    @property
    def db(self) -> SessionDatabase:
        """Get or create database connection."""
        if self._db is None:
            self._db = SessionDatabase(self.config)
            self._db.connect()
            # Populate conversation cache for tab completion
            self._refresh_conversation_cache()
        return self._db

    @property
    def cdp(self) -> SessionCDP:
        """Get or create CDP connection (lazy - only when needed)."""
        if self._cdp is None:
            try:
                self._cdp = SessionCDP(port=self.port)
                self._cdp.connect()
                print(f"Connected to Session CDP on port {self.port}")
            except Exception as e:
                print(f"Error: CDP connection failed: {e}")
                print(f"Start Session with: {SessionCDP.get_launch_command(self.port)}")
                raise
        return self._cdp

    def _refresh_conversation_cache(self) -> None:
        """Refresh conversation cache for tab completion."""
        try:
            convos = self.db.get_conversations()
            self._conversation_cache = convos
        except Exception:
            self._conversation_cache = []

    def _get_conversation_completions(self, text: str) -> list[str]:
        """Get conversation ID/name completions."""
        completions = []
        text_lower = text.lower()
        for c in self._conversation_cache:
            if c.id.lower().startswith(text_lower):
                completions.append(c.id)
            if c.name.lower().startswith(text_lower):
                completions.append(c.name)
        return completions

    def _find_conversation(self, id_or_name: str):
        """Find conversation by ID or name."""
        # Exact ID match
        convo = self.db.get_conversation(id_or_name)
        if convo:
            return convo

        # Partial match
        convos = self.db.get_conversations()
        matches = [
            c
            for c in convos
            if id_or_name.lower() in c.id.lower() or id_or_name.lower() in c.name.lower()
        ]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"Multiple matches for '{id_or_name}':")
            for c in matches:
                print(f"  - {c.name} ({c.id[:20]}...)")
            return None
        else:
            print(f"Conversation not found: {id_or_name}")
            return None

    def emptyline(self) -> bool:
        """Do nothing on empty line."""
        return False

    def default(self, line: str) -> bool:
        """Handle unknown commands."""
        print(f"Unknown command: {line.split()[0]}. Type 'help' for available commands.")
        return False

    # --- Commands ---

    def do_list(self, arg: str) -> bool:
        """List all conversations. Usage: list"""
        try:
            convos = self.db.get_conversations()
            self._conversation_cache = convos  # Update cache

            if self.json_output:
                print(json.dumps([c.raw for c in convos], indent=2))
                return False

            print(f"Found {len(convos)} conversations:\n")
            for c in convos:
                unread = f" ({c.unread_count} unread)" if c.unread_count else ""
                last = (
                    c.last_message[:40] + "..."
                    if c.last_message and len(c.last_message) > 40
                    else (c.last_message or "(empty)")
                )
                print(f"  [{c.type:8}] {c.name}")
                print(f"            ID: {c.id[:24]}...")
                print(f"            Last: {last}{unread}")
                print()
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_messages(self, arg: str) -> bool:
        """Show messages from a conversation. Usage: messages <id> [limit]"""
        args = shlex.split(arg) if arg else []
        if not args:
            print("Usage: messages <conversation_id> [limit]")
            return False

        convo_id = args[0]
        limit = int(args[1]) if len(args) > 1 else self.user_config.commands.messages_limit

        convo = self._find_conversation(convo_id)
        if not convo:
            return False

        try:
            messages = self.db.get_messages(convo.id, limit=limit)

            if self.json_output:
                print(json.dumps([m.raw for m in messages], indent=2))
                return False

            print(f"Messages from {convo.name} ({len(messages)} shown):\n")
            for msg in reversed(messages):
                time_str = msg.sent_at.strftime("%Y-%m-%d %H:%M")
                direction = "->" if msg.is_outgoing else "<-"
                sender = "You" if msg.is_outgoing else msg.source[:8]
                body = msg.body or "(no text)"

                print(f"[{time_str}] {direction} {sender}")
                print(f"  {body}")
                if msg.attachments:
                    print(f"  [attachment] {len(msg.attachments)} file(s)")
                print()
        except Exception as e:
            print(f"Error: {e}")
        return False

    def complete_messages(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Tab completion for messages command."""
        return self._get_conversation_completions(text)

    def do_send(self, arg: str) -> bool:
        """Send a message. Usage: send <id> <message>"""
        args = shlex.split(arg) if arg else []
        if len(args) < 2:
            print("Usage: send <conversation_id> <message>")
            return False

        convo_id = args[0]
        message = " ".join(args[1:])

        try:
            # Check conversation exists via database first
            convo = self._find_conversation(convo_id)
            if not convo:
                return False

            # Now connect to CDP and send
            result = self.cdp.send_message(convo.id, message)
            if result:
                print(f"Message sent to {convo.name}")
            else:
                print("Failed to send message")
        except CDPError as e:
            print(f"CDP Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def complete_send(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Tab completion for send command."""
        # Only complete the first argument (conversation ID)
        parts = line.split()
        if len(parts) <= 2:
            return self._get_conversation_completions(text)
        return []

    def do_search(self, arg: str) -> bool:
        """Search messages. Usage: search <query> [limit]"""
        args = shlex.split(arg) if arg else []
        if not args:
            print("Usage: search <query> [limit]")
            return False

        query = args[0]
        limit = int(args[1]) if len(args) > 1 else self.user_config.commands.search_limit

        try:
            results = self.db.search_messages_enhanced(query=query, limit=limit)

            if self.json_output:
                print(json.dumps([m.raw for m in results], indent=2))
                return False

            print(f"Found {len(results)} messages matching '{query}':\n")
            if not results:
                return False

            convos = {c.id: c.name for c in self._conversation_cache}

            for msg in results:
                time_str = msg.sent_at.strftime("%Y-%m-%d %H:%M")
                convo_name = convos.get(msg.conversation_id, msg.conversation_id[:12])
                body = msg.body[:60] if msg.body else "(no text)"

                print(f"[{time_str}] {convo_name}")
                print(f"  {body}...")
                print()
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_requests(self, arg: str) -> bool:
        """List pending requests. Usage: requests"""
        try:
            requests = self.db.get_pending_requests()

            if self.json_output:
                print(json.dumps([r.raw for r in requests], indent=2))
                return False

            if not requests:
                print("No pending requests.")
                return False

            print(f"Found {len(requests)} pending request(s):\n")
            for i, r in enumerate(requests, 1):
                req_type = ""
                if r.is_message_request:
                    req_type = " [Message Request]"
                elif r.is_contact_request:
                    req_type = " [Contact Request]"

                print(f"{i}. {r.name}{req_type}")
                print(f"   ID: {r.id}")
                print(f"   Type: {r.type}")
                if r.last_message:
                    last = r.last_message[:40] + "..." if len(r.last_message) > 40 else r.last_message
                    print(f"   Last message: {last}")
                print()
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_accept(self, arg: str) -> bool:
        """Accept a pending request. Usage: accept <id>"""
        if not arg:
            print("Usage: accept <request_id>")
            return False

        request_id = arg.strip()

        try:
            # Verify request exists
            request = self.db.get_request(request_id)
            if not request:
                print(f"Pending request not found: {request_id}")
                return False

            print(f"Accepting request from {request.name}...")
            result = self.cdp.accept_request(request_id)
            if result:
                print(f"Request accepted from {request.name}")
            else:
                print("Failed to accept request")
        except CDPError as e:
            print(f"CDP Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_info(self, arg: str) -> bool:
        """Show Session info. Usage: info"""
        try:
            print("Session Info:")
            print(f"  Data path: {self.config.data_path}")
            print(f"  Exists: {self.config.exists()}")

            if not self.config.exists():
                print("\n  Session data not found. Run Session at least once.")
                return False

            print(f"  Has password: {self.config.has_password}")

            our_id = self.db.get_our_pubkey()
            print(f"  Session ID: {our_id}")

            convos = self.db.get_conversations()
            print(f"  Conversations: {len(convos)}")

            # Check CDP status
            print("\n  CDP Status:")
            try:
                import urllib.request

                with urllib.request.urlopen(f"http://localhost:{self.port}/json", timeout=1):
                    print(f"    Available on port {self.port}")
            except Exception:
                print(f"    Not available (port {self.port})")
                print(f"    Start with: {SessionCDP.get_launch_command(self.port)}")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_json(self, arg: str) -> bool:
        """Toggle JSON output mode. Usage: json [on|off]"""
        arg = arg.strip().lower()
        if arg == "on":
            self.json_output = True
            print("JSON output enabled")
        elif arg == "off":
            self.json_output = False
            print("JSON output disabled")
        else:
            self.json_output = not self.json_output
            status = "enabled" if self.json_output else "disabled"
            print(f"JSON output {status}")
        return False

    def complete_json(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Tab completion for json command."""
        options = ["on", "off"]
        return [o for o in options if o.startswith(text.lower())]

    def do_refresh(self, arg: str) -> bool:
        """Refresh conversation cache. Usage: refresh"""
        try:
            self._refresh_conversation_cache()
            print(f"Refreshed cache: {len(self._conversation_cache)} conversations")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def do_stats(self, arg: str) -> bool:
        """
        Show messaging statistics. Usage: stats [options]

        Options:
          --top N       Show top N most active conversations
          --period Xd   Filter to last X days (e.g., 7d, 30d)
        """
        args = shlex.split(arg) if arg else []

        top = None
        period = None

        # Parse simple arguments
        i = 0
        while i < len(args):
            if args[i] == "--top" and i + 1 < len(args):
                top = int(args[i + 1])
                i += 2
            elif args[i] == "--period" and i + 1 < len(args):
                period = args[i + 1]
                i += 2
            else:
                i += 1

        try:
            # Parse period if specified
            after_timestamp = None
            if period:
                after_timestamp = self.db.parse_date_filter(period)

            stats = self.db.get_stats(after_timestamp=after_timestamp)

            if self.json_output:
                output = {"stats": stats}
                if top:
                    output["top_conversations"] = self.db.get_top_conversations(
                        limit=top, after_timestamp=after_timestamp
                    )
                print(json.dumps(output, indent=2))
                return False

            period_str = f" (last {period})" if period else ""
            print(f"Session Statistics{period_str}:\n")

            print("Overview:")
            print(f"  Total messages: {stats['total_messages']:,}")
            print(f"    Sent: {stats['sent']:,}")
            print(f"    Received: {stats['received']:,}")
            print(f"  With attachments: {stats['with_attachments']:,}")
            print(f"\n  Conversations: {stats['conversations']}")

            if stats['first_message']:
                print(f"\n  First message: {stats['first_message'][:10]}")
                print(f"  Last message: {stats['last_message'][:10]}")
                print(f"  Avg messages/day: {stats['avg_per_day']}")

            if stats['by_hour']:
                print("\nBusiest hours:")
                sorted_hours = sorted(stats['by_hour'].items(), key=lambda x: x[1], reverse=True)[:5]
                for hour, count in sorted_hours:
                    print(f"  {hour:02d}:00 - {count:,} messages")

            if top:
                print(f"\nTop {top} conversations:")
                top_convos = self.db.get_top_conversations(limit=top, after_timestamp=after_timestamp)
                for i, convo in enumerate(top_convos, 1):
                    print(f"  {i}. {convo['name']} - {convo['message_count']:,} messages")

        except Exception as e:
            print(f"Error: {e}")
        return False

    # === Group Management Commands ===

    def do_group(self, arg: str) -> bool:
        """
        Group management commands. Usage: group <command> [args]

        Commands:
          members <id>              - List group members and admins
          add <id> <session_id>     - Add member to group
          remove <id> <session_id>  - Remove member from group
          promote <id> <session_id> - Promote member to admin
          demote <id> <session_id>  - Demote admin to member
          leave <id>                - Leave a group
          create <name> <ids...>    - Create new group
          rename <id> <name>        - Rename a group
        """
        args = shlex.split(arg) if arg else []
        if not args:
            print("Usage: group <command> [args]")
            print("Commands: members, add, remove, promote, demote, leave, create, rename")
            print("Type 'help group' for details.")
            return False

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "members":
            return self._group_members(subargs)
        elif subcmd == "add":
            return self._group_add(subargs)
        elif subcmd == "remove":
            return self._group_remove(subargs)
        elif subcmd == "promote":
            return self._group_promote(subargs)
        elif subcmd == "demote":
            return self._group_demote(subargs)
        elif subcmd == "leave":
            return self._group_leave(subargs)
        elif subcmd == "create":
            return self._group_create(subargs)
        elif subcmd == "rename":
            return self._group_rename(subargs)
        else:
            print(f"Unknown group command: {subcmd}")
            print("Commands: members, add, remove, promote, demote, leave, create, rename")
            return False

    def _group_members(self, args: list[str]) -> bool:
        """List group members."""
        if not args:
            print("Usage: group members <group_id>")
            return False

        group_id = args[0]
        try:
            result = self.cdp.get_group_members(group_id)
            if not result:
                print(f"Group not found or not a group: {group_id}")
                return False

            if self.json_output:
                print(json.dumps(result, indent=2))
                return False

            print(f"Group: {result['name']}")
            print(f"ID: {result['id']}")
            print(f"You are admin: {'Yes' if result['weAreAdmin'] else 'No'}")
            print()

            print(f"Admins ({len(result['admins'])}):")
            for admin in result['admins']:
                print(f"  * {admin}")

            print(f"\nMembers ({len(result['members'])}):")
            for member in result['members']:
                is_admin = " (admin)" if member in result['admins'] else ""
                print(f"  - {member}{is_admin}")

        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_add(self, args: list[str]) -> bool:
        """Add member to group."""
        if len(args) < 2:
            print("Usage: group add <group_id> <session_id>")
            return False

        group_id, session_id = args[0], args[1]
        try:
            print(f"Adding {session_id} to group...")
            result = self.cdp.add_group_member(group_id, session_id)
            if result:
                print(f"Added {session_id} to group")
            else:
                print("Failed to add member")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_remove(self, args: list[str]) -> bool:
        """Remove member from group."""
        if len(args) < 2:
            print("Usage: group remove <group_id> <session_id>")
            return False

        group_id, session_id = args[0], args[1]
        try:
            print(f"Removing {session_id} from group...")
            result = self.cdp.remove_group_member(group_id, session_id)
            if result:
                print(f"Removed {session_id} from group")
            else:
                print("Failed to remove member")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_promote(self, args: list[str]) -> bool:
        """Promote member to admin."""
        if len(args) < 2:
            print("Usage: group promote <group_id> <session_id>")
            return False

        group_id, session_id = args[0], args[1]
        try:
            print(f"Promoting {session_id} to admin...")
            result = self.cdp.promote_to_admin(group_id, session_id)
            if result:
                print(f"Promoted {session_id} to admin")
            else:
                print("Failed to promote member")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_demote(self, args: list[str]) -> bool:
        """Demote admin to member."""
        if len(args) < 2:
            print("Usage: group demote <group_id> <session_id>")
            return False

        group_id, session_id = args[0], args[1]
        try:
            print(f"Demoting {session_id} from admin...")
            result = self.cdp.demote_admin(group_id, session_id)
            if result:
                print(f"Demoted {session_id} from admin")
            else:
                print("Failed to demote admin")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_leave(self, args: list[str]) -> bool:
        """Leave a group."""
        if not args:
            print("Usage: group leave <group_id>")
            return False

        group_id = args[0]
        try:
            # Get group info first
            info = self.cdp.get_group_members(group_id)
            if not info:
                print(f"Group not found: {group_id}")
                return False

            group_name = info['name']
            confirm = input(f"Leave group '{group_name}'? [y/N] ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return False

            print(f"Leaving group '{group_name}'...")
            result = self.cdp.leave_group(group_id)
            if result:
                print(f"Left group '{group_name}'")
            else:
                print("Failed to leave group")
        except Exception as e:
            print(f"Error: {e}")
        return False

    def _group_create(self, args: list[str]) -> bool:
        """Create a new group."""
        print("Group creation is not supported via CLI.")
        print("Session Desktop does not expose this API.")
        print("Please use the Session GUI to create groups.")
        return False

    def _group_rename(self, args: list[str]) -> bool:
        """Rename a group."""
        print("Group renaming is not supported via CLI.")
        print("Session Desktop does not expose this API for network sync.")
        print("Please use the Session GUI to rename groups.")
        return False

    def complete_group(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Tab completion for group command."""
        parts = line.split()
        if len(parts) <= 2:
            # Complete subcommand
            subcmds = ["members", "add", "remove", "promote", "demote", "leave", "create", "rename"]
            return [s for s in subcmds if s.startswith(text.lower())]
        return []

    def do_quit(self, arg: str) -> bool:
        """Exit the REPL. Usage: quit"""
        return self.do_exit(arg)

    def do_exit(self, arg: str) -> bool:
        """Exit the REPL. Usage: exit"""
        print("Goodbye!")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Handle Ctrl+D."""
        print()
        return self.do_exit(arg)

    # Aliases
    do_q = do_quit
    do_ls = do_list
    do_msg = do_messages
    complete_msg = complete_messages

    def cleanup(self) -> None:
        """Clean up connections."""
        if self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None

        if self._cdp is not None:
            try:
                self._cdp.close()
            except Exception:
                pass
            self._cdp = None

    def run(self) -> None:
        """Run the REPL with proper cleanup."""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nInterrupted. Goodbye!")
        finally:
            self.cleanup()
