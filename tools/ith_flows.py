"""ith_flows: writes the IT Help cloud flows (solution/src/Workflows) with tools/flow_builder.py. Project-specific (stage G9).

    uv run tools/ith_flows.py

The app writes one ITH_TicketActivity row for every event (AC-ITH-28); each flow triggers on a new row of its event types and emails the person who
needs to know (AC-ITH-32 to 34). Nothing else is read or written. The three flows share a mailbox variable (blank = the flow owner's mailbox), an app
link and a mail override (Dev and Test send every message to one tester; Production leaves it blank). Connector operation IDs and parameter names
are unverified without a tenant: confirm each flow in the designer after import (flow_builder.py header).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flow_builder as fb  # noqa: E402

fb.configure(env={"SharePoint site": "ith_SharePointSite", "ITH_Ticket": "ith_TicketList", "ITH_TicketActivity": "ith_TicketActivityList",
                  "Notification mailbox": "ith_NotificationMailbox", "App link": "ith_AppLink", "Mail override address": "ith_MailOverride"},
             sharepoint_ref="ith_sharepoint", outlook_ref="ith_office365outlook")
P, at, txt = fb.P, fb.at, fb.txt
ENV = ["SharePoint site", "ITH_Ticket", "ITH_TicketActivity", "Notification mailbox", "App link", "Mail override address"]
EV = "triggerOutputs()?['body/EventType/Value']"
TID = "triggerOutputs()?['body/TicketId']"
TICKET = "outputs('Get_the_ticket')?['body']"
TITLE = TICKET + "?['Title']"


def esc(x):
    """HTML-encode user text before it goes into an email body (a requester can type markup into a subject)."""
    return f"replace(replace(replace({x}, '&', '&amp;'), '<', '&lt;'), '>', '&gt;')"


def trigger(condition, desc):
    """A new ITH_TicketActivity row, filtered to the event types this flow handles by a trigger condition (so other events never start a run)."""
    return {"When_a_ticket_event_is_recorded": {
        "type": "OpenApiConnection", "description": desc, "recurrence": {"interval": 1, "frequency": "Minute"}, "splitOn": "@triggerOutputs()?['body/value']",
        "conditions": [{"expression": "@" + condition}],
        "inputs": {"host": {"connectionName": fb.SP, "operationId": "GetOnNewItems", "apiId": fb.API + fb.SP},
                   "parameters": {"dataset": at(P("SharePoint site")), "table": at(P("ITH_TicketActivity"))},
                   "authentication": "@parameters('$authentication')"}}}


def get_ticket(desc):
    return fb.sp("GetItem", {"table": at(P("ITH_Ticket")), "id": "@" + TID}, desc)


def link():
    return f"@{{parameters('App link (ith_AppLink)')}}?ticket=@{{{TID}}}"


def send(to_expr, subject, body, desc, with_from):
    """SendEmailV2; with the notification mailbox set it is sent as that mailbox (Send as), otherwise from the connection's own mailbox."""
    prm = {"emailMessage/To": fb.recipient(to_expr), "emailMessage/Subject": subject, "emailMessage/Body": body, "emailMessage/Importance": "Normal"}
    if with_from:
        prm["emailMessage/From"] = at(P("Notification mailbox"))
    return fb.ol("SendEmailV2", prm, desc)


def send_step(to_expr, subject, body, desc):
    """One step that picks the variant: the mailbox is set or not (a blank From would fail)."""
    return fb.cond("@empty(" + P("Notification mailbox") + ")",
                   [("Send_from_the_connection_mailbox", send(to_expr, subject, body, desc, False))],
                   [("Send_as_the_notification_mailbox", send(to_expr, subject, body, desc, True))], desc)


def html(lines):
    return "".join(f"<p>{ln}</p>" for ln in lines)


def created():
    body = html(["Your ticket has been created.", f"Ticket: HD-@{{{TID}}}<br>Subject: @{{{esc(TITLE)}}}", f"Open it: <a href=\"{link()}\">{link()}</a>"])
    steps = [("Get_the_ticket", get_ticket("AC-ITH-32.1 reads the new ticket to find its requester")),
             ("Email_the_requester", send_step(f"{TICKET}?['RequesterEmail']", f"Ticket HD-@{{{TID}}} created: @{{{TITLE}}}", body,
                                              "AC-ITH-32.1 and .2: confirmation to the requester with the ID, subject and a link"))]
    return fb.flow(ENV, trigger(f"equals({EV}, 'Created')", "AC-ITH-32.1 starts when a ticket is created"), steps, "The confirmation could not be sent.")


def assigned():
    who = "triggerOutputs()?['body/ActorEmail']"
    mail = f"{TICKET}?['AssignedToEmail']"
    body = html([f"A ticket has been assigned to you by @{{triggerOutputs()?['body/ActorName']}}.", f"Ticket: HD-@{{{TID}}}<br>Subject: @{{{esc(TITLE)}}}",
                 f"Open it: <a href=\"{link()}\">{link()}</a>"])
    mailstep = ("Email_the_assignee", send_step(mail, f"Ticket HD-@{{{TID}}} assigned to you: @{{{TITLE}}}", body, "AC-ITH-33.1 and .2: email to the new assignee with the ID, subject and a link"))
    steps = [("Get_the_ticket", get_ticket("AC-ITH-33.1 reads the ticket to find its assignee")),
             ("Only_if_someone_else_assigned_it", fb.cond(f"@and(not(empty({mail})), not(equals(toLower({mail}), toLower({who}))))", [mailstep], [],
                                                          "AC-ITH-33.3: no email when the ticket is unassigned or the assignee made the change (Q-19)"))]
    return fb.flow(ENV, trigger(f"and(or(equals({EV}, 'Assigned'), equals({EV}, 'AssigneeChanged')), not(empty(triggerOutputs()?['body/EventValue'])))",
                                "AC-ITH-33.1 starts when a ticket is assigned or reassigned to someone"), steps, "The assignment email could not be sent.")


def updated():
    who = "triggerOutputs()?['body/ActorEmail']"
    mail = f"{TICKET}?['RequesterEmail']"
    subj = f"@{{if(equals({EV}, 'Comment'), 'New comment on ', if(equals({EV}, 'Resolved'), 'Resolved: ', 'Status changed: '))}}HD-@{{{TID}}} @{{{TITLE}}}"
    what = (f"@{{if(equals({EV}, 'Comment'), concat(triggerOutputs()?['body/ActorName'], ' added a comment.'), "
            f"concat('The status is now ', triggerOutputs()?['body/EventValue'], '.'))}}")
    body = html([what, f"Ticket: HD-@{{{TID}}}<br>Subject: @{{{esc(TITLE)}}}", f"Open it: <a href=\"{link()}\">{link()}</a>"])
    mailstep = ("Email_the_requester", send_step(mail, subj, body, "AC-ITH-34.1 to .3: status, resolved or comment email with the ID, subject and a link"))
    steps = [("Get_the_ticket", get_ticket("AC-ITH-34.1 reads the ticket to find its requester")),
             ("Only_if_someone_else_made_the_change", fb.cond(f"@not(equals(toLower({mail}), toLower({who})))", [mailstep], [], "AC-ITH-34.4: no email to the person who made the change (Q-19)"))]
    return fb.flow(ENV, trigger(f"or(equals({EV}, 'StatusChanged'), equals({EV}, 'Resolved'), equals({EV}, 'Comment'))",
                                "AC-ITH-34.1 starts when a ticket's status changes, it is resolved, or a comment is added"), steps, "The update email could not be sent.")


def main():
    fb.write("Notify requester - ticket created", created())
    fb.write("Notify technician - ticket assigned", assigned())
    fb.write("Notify requester - ticket updated", updated())


if __name__ == "__main__":
    main()
