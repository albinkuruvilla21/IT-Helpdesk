"""flow_builder: write Power Automate cloud flows as solution components (solution/src/Workflows/<Name>-<GUID>.json + .json.data.xml).

Flows are JSON; writing them by hand is slow and error-prone. This module builds them from small steps and carries the rules learned
on the first project (docs/standards/flow-standard.md, powerapps-traps.md):
  * connections ONLY through connection references; every environment value is a parameter named "<Display name> (<schema>)" with an EMPTY default
    (P(display)); no site, list, mailbox, e-mail address or person in a step (`pp.py build` fails them: PA-T5, PA-T6);
  * every flow is a Try scope plus a Catch scope that ends in Terminate Failed (flow() does this); steps cite the AC ID in "description";
  * ORDER WRITES SAFELY (P8): send the e-mail first, then move the status, so a failure leaves the record unchanged and the flow re-runnable;
  * a flow the app calls has a Power Apps (V2) trigger: parameters are keyed "number", "text", "boolean", then "number_1", "text_1"...; the app passes
    them POSITIONALLY in the order declared; end with respond() so the app waits for completion and sees a failure as an error;
  * a trigger that modifies the item it fires on must be create-only (T-22); the shared-mailbox trigger polls (about a minute);
  * a mail override parameter (recipient()) lets Dev and Test send every message to one tester mailbox and Production leave it blank;
  * Choice columns are set with "item/<Column>/Value"; Number and Boolean columns with plain values; library files via CreateFile + PatchFileItem;
  * the app can call a flow only after it is ADDED TO THE APP in Studio, from an app opened from the imported solution (PA-T26).
  * UNVERIFIED without a tenant: the connector operation IDs and parameter names below were written from memory on the first project and must be
    confirmed by opening each flow in the designer after import: SharedMailboxOnNewEmailV2, GetItem, GetItems, PatchItem, GetFileItem, GetFileContent,
    CreateFile, PatchFileItem, GetItemAttachments, GetAttachmentContent, DeleteAttachment, SendEmailV2 (ReplyTo, Attachments). Fix them here once proven.

Use (from a project script, committed under tools/ or scripts/):
    import sys; sys.path.insert(0, "tools")
    import flow_builder as fb
    fb.configure(env={"SharePoint site": "prj_SharePointSite", "Request list": "prj_RequestList", "Mail override address": "prj_MailOverride"},
                 sharepoint_ref="prj_sharepoint", outlook_ref="prj_office365outlook")
    doc = fb.flow(["SharePoint site", "Request list"], fb.trigger_app([("number", "RequestItemId", "number", "NUMBER")]),
                  [("Get_the_request", fb.sp("GetItem", {"table": fb.at(fb.P("Request list")), "id": "@triggerBody()?['number']"}, "AC-XXX-01.1 ...")),
                   ("Respond_to_the_app", fb.respond())], "The thing could not be done.")
    fb.write("Request - Do the thing", doc)

    uv run tools/flow_builder.py --selftest
"""
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "/providers/Microsoft.PowerApps/apis/"
SP, OL = "shared_sharepointonline", "shared_office365"
CFG = {"env": {}, "sharepoint_ref": "prj_sharepoint", "outlook_ref": "prj_office365outlook", "override": "Mail override address", "root": ROOT}


def configure(env, sharepoint_ref, outlook_ref, override="Mail override address", root=None):
    """env: {display name: environment variable schema name}. Display names must match the variable definitions' display names."""
    CFG.update(env=dict(env), sharepoint_ref=sharepoint_ref, outlook_ref=outlook_ref, override=override, root=Path(root or ROOT))


def P(display):
    """The parameter expression for an environment variable."""
    return f"parameters('{display} ({CFG['env'][display]})')"


def at(expr):
    return "@" + expr


def txt(expr):
    return "@{" + expr + "}"


def recipient(real_expr):
    """The mail override (Dev/Test) wins over the real recipients."""
    o = P(CFG["override"])
    return txt(f"if(empty({o}), {real_expr}, {o})")


def step(host, op, params, desc, **extra):
    s = {"type": "OpenApiConnection", "description": desc,
         "inputs": {"host": {"connectionName": host, "operationId": op, "apiId": API + host}, "parameters": params,
                    "authentication": "@parameters('$authentication')"}}
    s.update(extra)
    return s


def sp(op, params, desc, site_display="SharePoint site", **extra):
    return step(SP, op, {"dataset": at(P(site_display)), **params}, desc, **extra)


def ol(op, params, desc, **extra):
    return step(OL, op, params, desc, **extra)


def chain(steps, first_after=None):
    """steps: [(name, action)]. Each runs after the one before it."""
    out, prev = {}, first_after
    for name, a in steps:
        a = dict(a)
        a["runAfter"] = {prev: ["Succeeded"]} if prev else {}
        out[name] = a
        prev = name
    return out


def terminate(status, code="", message=""):
    inputs = {"runStatus": status}
    if status == "Failed":
        inputs["runError"] = {"code": code, "message": message}
    return {"type": "Terminate", "inputs": inputs}


def cond(expression, yes, no, desc):
    return {"type": "If", "description": desc, "expression": expression, "actions": chain(yes), "else": {"actions": chain(no)}}


def foreach(name, items_expr, steps, desc):
    return {"type": "Foreach", "foreach": items_expr, "description": desc, "actions": chain(steps)}


def respond():
    return {"type": "Response", "kind": "PowerApp", "description": "Tells the app the work is done, so it can refresh and report.",
            "inputs": {"statusCode": 200, "body": {"ok": "@{true}"}, "schema": {"type": "object", "properties": {"ok": {"type": "string"}}}}}


def trigger_app(props):
    """props: [(key, title, type, hint)] e.g. ("number", "RequestItemId", "number", "NUMBER"), ("text", "Note", "string", "TEXT"), ("boolean", "Flag", "boolean", "BOOLEAN")."""
    return {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {
        "type": "object", "properties": {k: {"title": t, "type": ty, "x-ms-dynamically-added": True, "description": t, "x-ms-content-hint": h} for k, t, ty, h in props},
        "required": [k for k, *_ in props]}}}}


def trigger_new_mail(mailbox_display, folder="Inbox"):
    """A new e-mail in a SHARED mailbox (polls). Attachments arrive as triggerOutputs()?['body/attachments'] with name and contentBytes."""
    return {"When_a_new_email_arrives_in_the_shared_mailbox": {
        "type": "OpenApiConnection", "recurrence": {"interval": 1, "frequency": "Minute"}, "splitOn": "@triggerOutputs()?['body/value']",
        "inputs": {"host": {"connectionName": OL, "operationId": "SharedMailboxOnNewEmailV2", "apiId": API + OL},
                   "parameters": {"mailboxAddress": at(P(mailbox_display)), "folderPath": folder, "includeAttachments": True, "fetchOnlyWithAttachment": True},
                   "authentication": "@parameters('$authentication')"}}}


def flow(env_displays, triggers, try_steps, catch_message):
    """The whole flow document: parameters for the given environment variables, the trigger, a Try scope and a Catch scope that fails the run."""
    params = {"$connections": {"defaultValue": {}, "type": "Object"}, "$authentication": {"defaultValue": {}, "type": "SecureObject"}}
    for d in env_displays:
        params[f"{d} ({CFG['env'][d]})"] = {"defaultValue": "", "type": "String", "metadata": {"schemaName": CFG["env"][d]}}
    actions = {"Try": {"type": "Scope", "runAfter": {}, "actions": chain(try_steps)},
               "Catch": {"type": "Scope", "runAfter": {"Try": ["Failed", "TimedOut"]}, "actions": {
                   "Terminate_as_failed": {"type": "Terminate", "runAfter": {}, "inputs": {"runStatus": "Failed", "runError": {
                       "code": "FlowFailed", "message": "@{coalesce(result('Try')?[0]?['error']?['message'], '" + catch_message + "')}"}}}}}}
    return {"properties": {"connectionReferences": {
        SP: {"runtimeSource": "embedded", "connection": {"connectionReferenceLogicalName": CFG["sharepoint_ref"]}, "api": {"name": SP}},
        OL: {"runtimeSource": "embedded", "connection": {"connectionReferenceLogicalName": CFG["outlook_ref"]}, "api": {"name": OL}}},
        "definition": {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                       "contentVersion": "1.0.0.0", "parameters": params, "triggers": triggers, "actions": actions, "outputs": {}},
        "templateName": None}, "schemaVersion": "1.0.0.0"}


def write(display, doc):
    """Write <Name>-<GUID>.json and .json.data.xml and add the RootComponent. Re-running keeps a flow's GUID (found by its file name), so a flow keeps one identity."""
    wf = CFG["root"] / "solution" / "src" / "Workflows"
    wf.mkdir(parents=True, exist_ok=True)
    compact = re.sub(r"[^A-Za-z0-9]", "", display)
    existing = [f for f in wf.glob(f"{compact}-*.json") if not f.name.endswith(".data.xml")]
    guid = re.search(r"-([0-9A-F-]{36})\.json$", existing[0].name).group(1) if existing else str(uuid.uuid4()).upper()
    (wf / f"{compact}-{guid}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    xml = (ROOT / "samples" / "flows" / "SAMPLE-NotifyOnNewItem.json.data.xml").read_text(encoding="utf-8-sig")
    xml = xml.replace("89ed7cef-34a9-43d3-8cad-c7de90248aff", guid.lower()).replace("SampleNotifyOnNewItem-89ED7CEF-34A9-43D3-8CAD-C7DE90248AFF", f"{compact}-{guid}")
    xml = xml.replace("Sample - Notify on new item", display)
    (wf / f"{compact}-{guid}.json.data.xml").write_text("﻿" + xml, encoding="utf-8", newline="")
    sol = CFG["root"] / "solution" / "src" / "Other" / "Solution.xml"
    s = sol.read_text(encoding="utf-8-sig")
    line = f'<RootComponent type="29" id="{{{guid.lower()}}}" behavior="0" />'
    if line not in s:
        s = s.replace("<RootComponents>\n", "<RootComponents>\n      " + line + "\n", 1)
        sol.write_text("﻿" + s, encoding="utf-8", newline="")
    print("wrote", display, guid)


def selftest():
    configure({"SharePoint site": "tst_Site", "Item list": "tst_ItemList", "Mail override address": "tst_MailOverride"}, "tst_sharepoint", "tst_office365outlook")
    doc = flow(["SharePoint site", "Item list", "Mail override address"], trigger_app([("number", "ItemId", "number", "NUMBER")]),
               [("Get_the_item", sp("GetItem", {"table": at(P("Item list")), "id": "@triggerBody()?['number']"}, "AC-TST-01.1 reads it")),
                ("Email", ol("SendEmailV2", {"emailMessage/To": recipient("body('Get_the_item')?['Owner']")}, "AC-TST-01.2 emails")),
                ("Respond_to_the_app", respond())], "It failed.")
    d = doc["properties"]["definition"]
    assert list(d["actions"]["Try"]["actions"]) == ["Get_the_item", "Email", "Respond_to_the_app"]
    assert d["actions"]["Try"]["actions"]["Email"]["runAfter"] == {"Get_the_item": ["Succeeded"]}
    assert d["parameters"]["Item list (tst_ItemList)"]["defaultValue"] == ""
    assert d["actions"]["Catch"]["runAfter"] == {"Try": ["Failed", "TimedOut"]}
    assert doc["properties"]["connectionReferences"][SP]["connection"]["connectionReferenceLogicalName"] == "tst_sharepoint"
    assert "@" not in json.dumps(d["parameters"])
    print("flow_builder self-test: OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
