# Acies Innovations IT Help — prototype fidelity register

> Started by `/ingest` (stage **G1**) from the accepted prototype; AC IDs added by `/acceptance-criteria`
> (G2); *Built as* and *Status* kept by `/ui-dev` (G7) and `/functionality-dev` (G8); checked by `/verify`
> (check 17). The rules are in `docs/standards/prototype-fidelity.md`.
> One row per element or behaviour the prototype shows. Never delete a row: change its status.

| | |
|---|---|
| Prototype | `inputs/design/index (4).html` (single file, inline CSS and JS; acceptance date and version not recorded: PROJECT.md Q-01) |
| Inventoried | `2026-10-29` by `/ingest` |
| Views found | 13: 8 views (including the loading state) and 5 overlays (list in §1) |

Scale used by `prototype_design.py`: 1.5 (app content 1020 / prototype content 680). Fonts px × 1.5 × 0.75 = pt; lengths px × 1.5.
Wording below is verbatim from the prototype's source. "Prototype reference" is a CSS class, element id or script function in `index (4).html`.

## 1. Views

| View | Prototype reference | Reached from | Becomes |
|---|---|---|---|
| Loading state | `#ct` "Loading tickets…" (300 ms) | App start | Shown while data loads (`scrOverview` before data is ready) |
| Overview | `overview()` | Start; nav "Overview"; breadcrumb "Helpdesk" | `scrOverview` |
| All tickets | `listPage()` `V='all'` | Nav; "View all" on Recent tickets; empty-state buttons | `scrTickets` (mode `all`) |
| My tickets | `listPage()` `V='mine'` | Nav "My tickets" | `scrTickets` (mode `mine`) |
| Assigned to me | `listPage()` `V='assigned'` | Nav; "View all" on My assigned tickets | `scrTickets` (mode `assigned`) |
| Knowledge base | `kbPage()`, `kbList()` | Nav "Knowledge base" | `scrKnowledge` |
| Knowledge base article | `kbPage()` with `KO` set | A knowledge base card | `scrKnowledge` (article state) or `scrArticle` |
| Settings | `settings()` | Nav "Settings"; profile menu "Settings" | `scrSettings` |
| Create / Edit ticket (modal) | `openForm()`, `saveForm()` | "Create ticket" (header, empty state, article); row edit icon; drawer "Edit" | Overlay on any screen, `varModal` |
| Ticket detail (right drawer) | `drawer()`, `openT()` | Any ticket row; notification item | Overlay or `scrTicket` |
| Confirmation dialog (modal) | `confirmDlg()` | Close ticket, Delete, Reset demo data | Overlay, `varModal` |
| Notifications dropdown | `dd('dn')` `#dn` | Header bell | Overlay panel |
| Profile dropdown | `dd('dp')` `#dp` | Header avatar | Overlay panel |

## 2. Register

Kind: `layout` · `control` · `content` · `validation` · `action` · `navigation` · `conditional` · `list` ·
`derived` · `state` · `role` · `responsive` · `style` (the look: schemes, background, chrome, cards, buttons, badges, type scale; prototype-fidelity §8).
Status: `Not built` · `Built` · `Matched` · `Deviation` · `Out of scope` (prototype-fidelity §4).

### 2.1 Shell (sidebar, header, global)

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-01 | Shell | Two regions side by side: left sidebar `aside` then `.main` (header above content) | layout | `.app` | | | Not built | |
| P-02 | Shell | Sidebar 232 px wide (348 scaled), white card colour, 1 px right border, padding 12, gap 4 | layout | `aside` | | | Not built | |
| P-03 | Shell | Logo: 28 px square tile, radius 8, accent fill, white "H"; beside it bold "Helpdesk" (15 px, weight 600) | content | `.logo`, `.mark` | | | Not built | |
| P-04 | Shell | Nav items in order: "Overview", "All tickets", "My tickets", "Assigned to me", "Knowledge base", "Settings"; icons home, list, user, check, book, gear | list | `NAV`, `nav()` | | | Not built | |
| P-05 | Shell | Active nav item: accent-soft fill, accent text, weight 500, `aria-current="page"`; inactive text muted; hover fills with hover colour | state | `.nav.on`, `.nav:hover` | | | Not built | |
| P-06 | Shell | Count pill on "My tickets" (my tickets not Resolved/Closed) and "Assigned to me" (assigned to me, not Resolved/Closed); hidden when 0 | derived | `nav()`, `mine()`, `asg()`, `live()` | | | Not built | 12 px, radius 10, hover-colour fill; on the active item fill is card colour |
| P-07 | Shell | Profile block pinned to sidebar bottom: avatar "AM", name "Alex Morgan" bold, "IT technician" small muted; top border | layout | `.prof` | | | Not built | In production: signed-in user's name and role |
| P-08 | Shell | Sidebar collapse: button (menu icon, label "Collapse sidebar") toggles a 64 px rail (96 scaled) showing icons only (labels, counts and "Helpdesk" text hidden); animates width .2 s | action | `#tg`, `.col aside` | | | Not built | BRD R3: "subject to Power Apps control support" |
| P-09 | Shell | Sidebar starts collapsed when viewport width is under 700 px | responsive | `if(innerWidth<700)` | | | Not built | |
| P-10 | Shell | Header 60 px (90 scaled) high, card colour, 1 px bottom border, padding 0 20, gap 12 | layout | `.hd` | | | Not built | |
| P-11 | Shell | Header left to right: collapse button, breadcrumb, search box (pushed right, 300 px), "Create ticket" primary button, theme toggle, bell, avatar | layout | `header.hd` | | | Not built | |
| P-12 | Shell | Breadcrumb: link "Helpdesk" (goes to Overview) then " / " then bold page title; for an open article "Knowledge base / <article title>"; titles: "Overview", "All tickets", "My tickets", "Assigned to me", "Knowledge base", "Settings" | navigation | `.crumb`, `#title`, `TT`, `render()` | | | Not built | Hidden under 700 px |
| P-13 | Shell | Global search box, search icon, placeholder "Search tickets by ID or subject", label "Search tickets"; typing sets the shared query and, if not on All/My/Assigned, navigates to All tickets | action | `#gq`, `setQ()` | | | Not built | Same query is mirrored in the list's own search box |
| P-14 | Shell | Search box focus: accent border and 3 px accent ring (`#4f46e51f`) | state | `.sbox:focus-within` | | | Not built | |
| P-15 | Shell | Primary button "Create ticket" with plus icon opens the Create ticket modal; text hidden under 700 px (icon only) | action | `openForm()`, `.btn.p .lbl` | | | Not built | |
| P-16 | Shell | Theme toggle button (moon icon in light, sun icon in dark), label "Toggle dark theme"; switches scheme and re-renders | action | `#th`, `toggleTheme()`, `applyTheme()` | | | Not built | BRD R2 says dark theme out of scope: Q-04 |
| P-17 | Shell | Notification bell, label "Notifications", red 8 px dot top-right until opened once | state | `dd('dn')`, `#dot`, `READ` | | | Not built | |
| P-18 | Shell | Notifications panel (300 px, radius 10, shadow `0 8px 24px #10182814`): the 5 most recent activity entries across all tickets, each a row with the text, and under it small "HD-nnnn · <relative time>"; click opens that ticket's drawer | list | `feed(5)`, `rel()` | | | Not built | Relative time: "just now", "n min ago", "n h ago", "n d ago" |
| P-19 | Shell | Avatar button, label "Profile", opens menu (300 px): bold "Alex Morgan", small "alex.morgan@contoso.com", buttons "Settings" and "Reset demo data" | action | `dd('dp')`, `#dp` | | | Not built | |
| P-20 | Shell | "Reset demo data" in profile menu and Settings: confirm "Reset demo data?" / "All tickets return to the sample set. Your changes are lost." / button "Reset"; result toast "Demo data restored" | action | `resetData()` | | | Not built | Demo-only: Out of scope in production unless the PO wants it (Q-05) |
| P-21 | Shell | Only one dropdown open at a time; clicking outside closes it; navigating closes it | conditional | `document` click handler, `go()` | | | Not built | |
| P-22 | Shell | `Escape` closes the open modal, else the open drawer | action | `keydown` handler | | | Not built | Keyboard reachability (D9) |
| P-23 | Shell | Toasts stack bottom-right (16 px from edges), auto-dismiss after 3.2 s; dark navy fill white text, error toasts red; `role="status"` `aria-live="polite"` | state | `toast()`, `#ts`, `.toast`, `.toast.err` | | | Not built | `Notify` |
| P-24 | Shell | Loading state: content area shows centred "Loading tickets…" for 300 ms at start | state | `$('#ct').innerHTML`, `setTimeout(render,300)` | | | Not built | |
| P-25 | Shell | Saved data unreadable: toast (error) "Saved data could not be read. Sample data restored." | state | `load()` | | | Not built | Browser-storage specific; Out of scope in production |
| P-26 | Shell | Save failure: toast (error) "Could not save changes in this browser." | state | `save()` | | | Not built | Becomes a SharePoint write-failure message |

### 2.2 Overview

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-30 | Overview | Four stat cards in one row (equal columns, gap 14): "Total tickets", "Open", "In progress", "Resolved today"; label muted above a 26 px weight-600 number | layout | `overview()`, `.g4`, `.stat` | | | Not built | |
| P-31 | Overview | Stat values: Total = all tickets; Open = status Open; In progress = status In Progress; Resolved today = status Resolved and last updated today | derived | `overview()` `n()`, `rt` | | | Not built | BRD R4: requesters see only own tickets; Q-06 |
| P-32 | Overview | Under 900 px the stat row becomes 2 columns | responsive | `@media(max-width:900px)` | | | Not built | |
| P-33 | Overview | Second row, two cards 2fr : 1fr. Left card "Recent tickets" with small button "View all" (goes to All tickets) | layout | `.g2` | | | Not built | |
| P-34 | Overview | Recent tickets list: 6 most recently created; row = ticket ID (accent, weight 500), subject (truncated, max 300 px), priority badge (hidden under 700 px), status badge; click or `Enter` opens the drawer; empty: "Nothing here yet." | list | `mini()` | | | Not built | |
| P-35 | Overview | Right card "Tickets by status": for each of Open, In Progress, On Hold, Resolved, Closed a row of label (90 px), 8 px progress bar whose width is count/total, and the count right-aligned bold | list | `.br`, `.tr` | | | Not built | Bar colours = status colours (P-92) |
| P-36 | Overview | Same card, heading "Tickets by priority": stacked 12 px bar split by Low, Medium, High, Critical (`role="img"`, `aria-label="Priority split"`), legend below: coloured square plus "<Priority> <count>" | list | `.stk`, `.lg` | | | Not built | Add a text equivalent (D9) |
| P-37 | Overview | Third row, two equal cards. Left "My assigned tickets" with "View all" (goes to Assigned to me): first 5 assigned-to-me tickets not Resolved/Closed, same row as P-34 | list | `asg().filter(live).slice(0,5)` | | | Not built | |
| P-38 | Overview | Right card "Recent activity": 7 latest activity entries across all tickets, each a small accent dot, the text, and under it small muted "HD-nnnn · <relative time>" | list | `feed(7)`, `.ev` | | | Not built | |
| P-39 | Overview | Under 900 px the two-card rows stack to one column | responsive | `@media(max-width:900px)` | | | Not built | |

### 2.3 Ticket lists (All tickets, My tickets, Assigned to me)

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-40 | Lists | Page heading (h1 18 px) = view title, muted description under it: All "Every ticket in the helpdesk.", My "Tickets you submitted as Alex Morgan.", Assigned "Tickets assigned to you." | content | `listPage()`, `DESC` | | | Not built | Name is the signed-in user's |
| P-41 | Lists | Toolbar: search box (280 px) "Search by ID or subject", then three selects, then ghost button "Clear filters" | layout | `.tb` | | | Not built | |
| P-42 | Lists | Status filter select, first option "All statuses" then Open, In Progress, On Hold, Resolved, Closed; label "Status" | control | `STS` | | | Not built | Options from the status list (BRD R19) |
| P-43 | Lists | Priority filter select "All priorities" then Low, Medium, High, Critical; label "Priority" | control | `PRIS` | | | Not built | |
| P-44 | Lists | Category filter select "All categories" then Hardware, Software, Network, Access, Other; label "Category" | control | `CATS` | | | Not built | |
| P-45 | Lists | "Clear filters" empties search, status, priority, category, resets to page 1 and clears the global search box | action | `clr()` | | | Not built | |
| P-46 | Lists | Search matches ticket ID or subject, case-insensitive substring; any filter change resets to page 1 | action | `renderTable()` | | | Not built | Delegation: Q-07 |
| P-47 | Lists | Base set per view: All = every ticket; My = requester email equals signed-in user's; Assigned = assigned to signed-in user (including Resolved and Closed) | derived | `mine()`, `asg()` | | | Not built | Count pills (P-06) exclude Resolved/Closed; the list does not |
| P-48 | Lists | Table columns in order: "Ticket ID", "Subject", "Requester", "Category", "Priority", "Assigned to", "Status", "Created", "Actions"; Requester, Category, Assigned to, Created hidden under 700 px | list | `C` array in `renderTable()` | | | Not built | |
| P-49 | Lists | Header cells are sortable (all but Actions): click sorts ascending, click again reverses; ▲ / ▼ shown in the active header; `aria-sort`. Default sort: Created, newest first. Sort keys: ID numeric, Priority and Status by list order (not alphabetical), others text lower-case | action | `sortBy()`, `sv()`, `F.sort`, `F.dir` | | | Not built | |
| P-50 | Lists | Header row: 12.5 px muted, weight 500, background header-3 colour, 1 px bottom border | style | `th` | | | Not built | |
| P-51 | Lists | Row: ID accent weight 500; subject truncated 300 px; requester; category; priority badge; "Assigned to" name or muted "Unassigned"; status badge; Created as `dd Mon yyyy` (en-GB); hover row fill; pointer cursor | list | `renderTable()`, `sd()` | | | Not built | |
| P-52 | Lists | Row click or `Enter` (rows are focusable) opens the ticket drawer | navigation | `openT()` | | | Not built | |
| P-53 | Lists | Row actions: ghost icon button edit (label "Edit HD-nnnn") opens Edit modal; red ghost icon button trash (label "Delete HD-nnnn") opens delete confirmation; neither opens the drawer | action | `openForm(id)`, `delT(id)` | | | Not built | Delete: Administrators only (BRD R14, R20); edit: Q-08 |
| P-54 | Lists | Footer: "<from>–<to> of <total>", then right-aligned "Rows" select (5, 10, 25; default 10), previous button (label "Previous page", disabled on page 1), "<page> / <pages>", next button (label "Next page", disabled on last page) | list | `.pg` | | | Not built | |
| P-55 | Lists | Empty state, filters active: icon inbox, heading "No tickets match your filters", text "Try a different search or clear the filters.", button "Clear filters" | state | `renderTable()` `!n` | | | Not built | |
| P-56 | Lists | Empty state, no filters: heading "No tickets here yet", text "Create a ticket to get started.", primary button "Create ticket" | state | `renderTable()` `!n` | | | Not built | |

### 2.4 Create / Edit ticket modal

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-60 | Modal | Centred modal over a dimmed overlay (`#10182866`), width up to 560, radius 12, padding 20, shadow `0 20px 50px #10182833`; clicking the overlay closes it; `role="dialog"` | layout | `modal()`, `.modal` | | | Not built | |
| P-61 | Modal | Title row: heading "Create ticket" (new) or "Edit HD-nnnn" (edit), close icon button (label "Close") | content | `openForm()` | | | Not built | |
| P-62 | Modal | Field "Ticket subject *", single-line, placeholder "Short summary of the issue", focused on open | control | `#f_subject` | | | Not built | |
| P-63 | Modal | Field "Description *", 4-row textarea, placeholder "What happened, and what did you expect?" | control | `#f_description` | | | Not built | |
| P-64 | Modal | Two-up row: "Category" select (Hardware, Software, Network, Access, Other; default Software) and "Priority" select (Low, Medium, High, Critical; default Medium) | control | `#f_category`, `#f_priority` | | | Not built | Q-09: may requesters set priority |
| P-65 | Modal | Two-up row: "Requester name" (default signed-in name) and "Requester email" (default signed-in email) | control | `#f_requesterName`, `#f_requesterEmail` | | | Not built | BRD R6: default to signed-in user |
| P-66 | Modal | "Assign to (optional)" select: first option "Unassigned", then the four technicians (Alex Morgan, Priya Nair, Daniel Kim, Sofia Rossi) | control | `#f_assignedTo`, `TECHS` | | | Not built | Technician list from SharePoint (BRD R19) |
| P-67 | Modal | New ticket only: "Attachments" file input (multiple) with small muted text "Simulated: file names are saved, files are not uploaded." | control | `#f_att` | | | Not built | Production stores real files (BRD R8); the help text is dropped (Deviation to record) |
| P-68 | Modal | Footer buttons right-aligned: "Cancel" and primary "Create ticket" (new) or "Save changes" (edit) | action | `.ft` | | | Not built | |
| P-69 | Modal | Validation, on submit only: subject empty after trim: "Enter a subject." under the field | validation | `saveForm()` | | | Not built | Field border turns red (`#dc2626`) |
| P-70 | Modal | Validation: description empty after trim: "Describe the issue." | validation | `saveForm()` | | | Not built | |
| P-71 | Modal | Validation: requester email entered and not matching `^\S+@\S+\.\S+$`: "Enter a valid email address." (empty email is allowed, falls back to the signed-in email) | validation | `saveForm()` | | | Not built | |
| P-72 | Modal | Errors cleared per field on the next submit; nothing saves while any error shows; modal stays open | validation | `saveForm()` | | | Not built | |
| P-73 | Modal | Blank requester name falls back to signed-in name; blank email to signed-in email | derived | `saveForm()` | | | Not built | |
| P-74 | Modal | Create: new ID `HD-` + (highest number, at least 1000, plus 1); status "Open"; created and updated = now; attachments = file names and size in KB (at least 1 KB); activity entry "<requester name> created the ticket"; if assigned, a second entry "Alex Morgan assigned the ticket to <name>"; toast "HD-nnnn created"; modal closes and the current view refreshes | action | `saveForm()` | | | Not built | BRD R6: ID by flow or Power Fx; race on concurrent creates (Q-10) |
| P-75 | Modal | Edit: overwrites subject, description, category, priority, requester name and email, assignee; activity entry "Alex Morgan edited ticket details"; updated = now; toast "HD-nnnn updated" | action | `saveForm()` | | | Not built | Edit does not log an assignment-change entry in the prototype |
| P-76 | Modal | Opening the form from a knowledge base article prefills the subject with the article title | action | `openForm(null, title)` | | | Not built | |
| P-77 | Modal | Under 700 px the two-up rows become one column | responsive | `.two` | | | Not built | |

### 2.5 Ticket detail drawer

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-80 | Drawer | Panel slides in from the right over a dimmed overlay, width up to 580, full height, scrolls; click outside or `Escape` closes; entrance animation .18 s (off under reduced motion) | layout | `drawer()`, `.drawer` | | | Not built | |
| P-81 | Drawer | Top row: ticket ID (accent, weight 500) and close icon button (label "Close panel"); heading = subject; under it status badge and priority badge | content | `drawer()` | | | Not built | |
| P-82 | Drawer | Action buttons: "Edit" (pencil icon), "Resolve" (only while Open/In Progress/On Hold), "Close ticket" (unless already Closed), red "Delete" (trash icon) | action | `drawer()` | | | Not built | Role gating: BRD R9, R10, R14, R20 |
| P-83 | Drawer | "Resolve" sets status Resolved at once, toast "HD-nnnn marked Resolved" | action | `setF('status','Resolved')` | | | Not built | |
| P-84 | Drawer | "Close ticket" opens confirmation: title "Close HD-nnnn?", text "Closed tickets are treated as complete. You can reopen it by changing the status.", buttons "Cancel" and "Close ticket"; confirm sets status Closed | action | `closeTk()`, `confirmDlg()` | | | Not built | |
| P-85 | Drawer | "Delete": confirmation title "Delete HD-nnnn?", text "This permanently removes the ticket, its comments, and its activity.", buttons "Cancel" and "Delete ticket"; confirm removes the ticket, closes the drawer, toast "HD-nnnn deleted" | action | `delT()` | | | Not built | Q-11: permanent delete or retain |
| P-86 | Drawer | Two-column detail grid: "Status" select, "Priority" select, "Assigned technician" select (first option "Unassigned"), "Category" (text), "Requester" (name, and email muted beneath), "Created" (date and time) with "Last updated" beneath; small muted labels | layout | `.kv` | | | Not built | One column under 700 px |
| P-87 | Drawer | Changing status, priority or assignee saves at once; no-op if unchanged; activity entry "Alex Morgan changed status to <v>" / "priority to <v>" / "assignee to <v or Unassigned>"; updated = now; toast "HD-nnnn marked <status>" for status, else "Ticket updated" | action | `setF()` | | | Not built | Requesters cannot change these (BRD R9) |
| P-88 | Drawer | Section "Description": full text, line breaks kept | content | `drawer()` | | | Not built | |
| P-89 | Drawer | Section "Attachments": each as a bordered row with file name and small size ("184 KB"); none: "No attachments." | list | `drawer()` | | | Not built | |
| P-90 | Drawer | Section "Comments (n)": each comment bordered, bold author, small date and time, text; none: "No comments yet."; then a 3-row textarea (placeholder "Write a comment", label "Comment") and primary "Add comment" | list | `addC()` | | | Not built | |
| P-91 | Drawer | Add comment: empty after trim shows error toast "Write a comment before adding it."; else adds, logs "Alex Morgan added a comment", toast "Comment added", refreshes | validation | `addC()` | | | Not built | |
| P-92 | Drawer | Section "Activity": vertical timeline, newest first, each entry text and small date and time, 8 px accent dot on a 2 px left rule | list | `.tl` | | | Not built | |
| P-93 | Drawer | Dates: date and time as `dd Mon yyyy, hh:mm` (en-GB); dates only as `dd Mon yyyy` | derived | `fmt()`, `sd()` | | | Not built | |
| P-94 | Drawer | Drawer opens over the current view and the underlying list refreshes after each change | state | `render()` | | | Not built | |

### 2.6 Knowledge base

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-100 | KB | Heading "Knowledge base", muted "Self-service guides for common issues." | content | `kbPage()` | | | Not built | |
| P-101 | KB | Toolbar: search box placeholder "Search articles" (label "Search articles", matches title or description) and category chips "All", Account, Network, Email, Software (in order of first appearance); selected chip accent-soft fill | control | `kbList()`, `.chip` | | | Not built | Chips derived from the articles' categories |
| P-102 | KB | Article cards in an auto-fill grid (min 260 px, gap 14): category (muted), title (h3), short description; click opens the article | list | `.kb` | | | Not built | |
| P-103 | KB | Empty: `No articles match "<query>".` spanning the grid | state | `kbList()` | | | Not built | |
| P-104 | KB | Six articles in order: Account "How to reset your password"; Network "Troubleshooting VPN connectivity"; Email "Setting up Outlook"; Software "Requesting software access"; Network "Connecting to office Wi-Fi"; Account "Setting up multi-factor authentication" (descriptions and steps in the script's `KB` array) | content | `KB` | | | Not built | Initial articles to be supplied by the client (BRD R18) |
| P-105 | KB article | Ghost button "Back to articles" (left chevron); heading (22 px) = title; muted "<category> · <description>"; a card with the numbered steps | layout | `kbPage()` `KO!=null` | | | Not built | |
| P-106 | KB article | Closing card: "Still stuck?" and primary "Create ticket" which opens the form with the subject prefilled (P-76) | action | `openForm(null,title)` | | | Not built | |

### 2.7 Settings

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-110 | Settings | Heading "Settings", muted "Reference information for this prototype." | content | `settings()` | | | Not built | Wording "for this prototype" changes (Deviation) |
| P-111 | Settings | Row of three cards: "Current user" (avatar, bold name, muted email, "Role: IT technician"); "Ticket categories" (chips Hardware, Software, Network, Access, Other); "Simulated behaviour" (text "Sign-in, email, and attachments are simulated. Ticket data is saved in this browser only." and red "Reset demo data") | layout | `.g3` | | | Not built | Third card is prototype-only: Q-05 |
| P-112 | Settings | Second row, two equal cards: "Priority definitions" and "Status definitions"; each line = coloured badge then muted definition | list | `PD`, `SD` | | | Not built | |
| P-113 | Settings | Priority definitions: Low "Minor issue or question with a workaround. Target: 3 days."; Medium "Affects one person's work, no workaround. Target: 1 day."; High "Blocks a person or small team. Target: 4 hours."; Critical "Business-wide outage or security risk. Target: 1 hour." | content | `PD` | | | Not built | Targets are text only (BRD R19) |
| P-114 | Settings | Status definitions: Open "Submitted and waiting to be picked up."; In Progress "A technician is actively working on it."; On Hold "Waiting on the requester, a vendor, or parts."; Resolved "A fix is in place and awaiting confirmation."; Closed "Confirmed complete. No further work." | content | `SD` | | | Not built | |

### 2.8 Roles, data and behaviour not shown

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-120 | All | The prototype has one fixed user, "Alex Morgan", an IT technician, who can do everything including delete | role | `ME` | | | Not built | BRD R20 adds Requester, Technician, Administrator: the differences are not in the prototype (Q-03) |
| P-121 | All | Notifications are an in-app feed of activity entries only; no email | derived | `feed()` | | | Not built | Outlook emails (BRD R17) have no prototype view: AC from BRD |
| P-122 | All | Seed data: 14 sample tickets HD-1001 to HD-1014, mixed statuses/priorities/categories, some with an attachment "screenshot.png" (184 KB) and comments | content | `seed()` | | | Not built | Sample rows only for the build; no client data |
| P-123 | All | Data kept in `localStorage` key `hd_tickets_v1`; theme in `hd_theme` | state | `KEY`, `save()`, `load()` | | | Not built | Becomes SharePoint lists; theme choice per user is Q-04 |
| P-124 | All | Keyboard: nav, rows, buttons and inputs are focusable with a visible 2 px accent outline (1 px offset); table rows respond to `Enter` | state | `:focus-visible`, `onkeydown` | | | Not built | D9 |
| P-125 | All | Animations (drawer slide, toast, sidebar width) off under `prefers-reduced-motion` | responsive | `@media(prefers-reduced-motion)` | | | Not built | |

### 2.9 The look (style rows)

Measured with `tools/prototype_design.py` (`specs/prototype-design.json`). The prototype switches scheme by `data-theme="dark"` on `<html>`, which the tool did not detect: the dark values below are read from the CSS by hand.

| P-ID | View | Element or behaviour | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-130 | All | Light scheme: bg `#f6f7f9`, card `#ffffff`, border `#e4e7ec`, text `#101828`, muted `#667085`, accent `#4f46e5`, accent hover `#4338ca`, accent soft `#eef2ff`, hover `#f2f4f7`, hover-2 `#f9fafb`, hover-3 `#fcfcfd`, line `#f0f2f5` | style | `:root` | | | Not built | |
| P-131 | All | Dark scheme: bg `#0b0f17`, card `#121826`, border `#263041`, text `#e6e9ef`, muted `#98a2b3`, accent `#818cf8`, accent hover `#4338ca`, accent soft `#1e2347`, hover `#1b2335`, hover-2 `#161d2c`, hover-3 `#151b29`, line `#1c2434`; primary button fill stays `#4f46e5`; danger text and error text `#fca5a5`; toast `#2a3347`; overlay `#000a` | style | `[data-theme=dark]` | | | Not built | Chosen by configuration, not the device (platform limit) |
| P-132 | All | Status and priority colours, light: Open `#1d4ed8`, In Progress `#b45309`, On Hold `#475467`, Resolved `#15803d`, Closed `#667085`, Low `#475467`, Medium `#1d4ed8`, High `#c2410c`, Critical `#b91c1c`; dark: Open `#93c5fd`, In Progress `#fcd34d`, On Hold `#cbd5e1`, Resolved `#86efac`, Closed `#94a3b8`, Low `#cbd5e1`, Medium `#93c5fd`, High `#fdba74`, Critical `#fca5a5` | style | `CL`, `CLt`, `CD` | | | Not built | |
| P-133 | All | Badge: pill radius 12 (18 scaled), padding 1 × 9, 12.5 px weight 500, 6 px dot then the word; text in the colour, fill = that colour at 14 % mixed into the card colour | style | `.b`, `bd()` | | | Not built | Translucent mix: compute the blended hex per scheme |
| P-134 | All | Type: Inter 400/500/600, 14 px body (16 pt), h1 18 px (20 pt, 600), h3 14 px (16 pt, 600), logo 15 px (17 pt), stat number 26 px (29 pt, 600), table head 12.5 px (14 pt, 500), small 12 px (13.5 pt) | style | `body`, `h1`, `.stat b` | | | Not built | Inter is not a Studio font: nearest is `Segoe UI` (tool match). Record in design-spec |
| P-135 | All | Cards: card colour, 1 px border, radius 10 (15 scaled), padding 16 (24 scaled); no shadow. Card header: padding 12 × 16, bottom border | style | `.card`, `.cp`, `.ch` | | | Not built | |
| P-136 | All | Buttons: radius 8 (12), padding 7 × 12, weight 500, 1 px border; primary accent fill white text; ghost has no border, muted text; small padding 3 × 8; danger text `#b91c1c` | style | `.btn` | | | Not built | |
| P-137 | All | Fields: 1 px border, radius 8 (12), padding 7 × 10 (10 × 15), card fill | style | `select`, `input`, `textarea` | | | Not built | |
| P-138 | All | Shadows only on dropdowns (`0 8px 24px #10182814`), modal (`0 20px 50px #10182833`), toast (`0 8px 24px #10182833`) | style | `.dd`, `.modal`, `.toast` | | | Not built | |
| P-139 | All | Page background is a flat colour (no gradient, no image, no blur); sidebar and header are flat card-colour bands with 1 px borders | style | `body`, `aside`, `.hd` | | | Not built | `chrome`/`topbar` pattern; no backdrop blur needed |
| P-140 | All | Logo tile 28 px (42 scaled), radius 8 (12), accent fill, white "H"; avatar 30 px circle, accent-soft fill, accent initials 12 px weight 600 | style | `.mark`, `.av` | | | Not built | `svg_tile` |
| P-141 | All | Icons: line icons, 1.8 stroke, sizes 14–32: home, list, user, check, book, gear, search, bell, plus, x, chevron left/right, menu (sidebar), trash, edit, inbox, sun, moon | style | `P` icon map | | | Not built | Closest built-in icons, with accessible names |
| P-142 | All | Disabled buttons at 50 % opacity | state | `.btn:disabled` | | | Not built | |

## 3. Deviations

Every `Deviation` row, with its design-spec §9 row. The reason must be one prototype-fidelity §6 allows.

| P-ID | Prototype shows | Built as | Reason | design-spec §9 |
|---|---|---|---|---|

## 4. Not in the acceptance criteria

Rows with no AC ID: why, and the proposed change or question that covers each. (To be completed by `/acceptance-criteria`.)

| P-ID | Why no AC ID | Proposed change / Q-nn |
|---|---|---|
| P-20, P-111 (third card), P-25, P-123 | Demo-only behaviour (reset demo data, browser storage) | Q-05 |
| P-16, P-131 | BRD R2 puts dark theme out of scope; the prototype ships it | Q-04 |
