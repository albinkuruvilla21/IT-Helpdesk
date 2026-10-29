# Proposed changes to the acceptance criteria (2026-10-29)

Written by `/deliver` after G2 was approved. The workbook is not edited by Claude; the BA and PO apply these in Excel (status `Changed`, a dated Alterations line).

| AC ID | Proposed change | Source | Downstream impact |
|---|---|---|---|
| AC-ITH-30 | Set `Out of Scope` (or rewrite): tickets are not deleted; they are closed and kept for audit. Remove the red "Delete" button, the list row delete icon and the "Delete <ID>?" confirmation | Q-11 answered 2026-10-29: "Only closed and kept for audit." | `scrTickets`, `scrTicket`; nothing built for delete |
| AC-ITH-41 | Check 2 ("An administrator can delete tickets") removed; check 3 keeps master data and articles | Q-11 | Role logic |
| AC-ITH-18 | Check 3 and 5: only the edit icon remains on a row | Q-11 | `scrTickets` |
| AC-ITH-28 | Check 4: activity entries are never removed (tickets are never deleted) | Q-11 | None |
| AC-ITH-05, 39, 40, 41 | Role comes from the SharePoint list `ITH_UserRoles` (email, role) until groups are given | Q-03 answered | New list `ITH_UserRoles` |
| AC-ITH-10 | Phone layout out of scope. The prototype's 900 px and 700 px rearrangements are not built; the app is one layout | Q-04 answered | `scrOverview`, `scrTickets` |
| AC-ITH-44 | Already "not built"; Q-05 answered "Not needed" | Q-05 | None |
