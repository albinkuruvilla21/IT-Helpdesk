# releases/

One pair of solution ZIPs per release candidate, written and committed by `/verify release` (stage G11) with that
version's `specs/release-notes.md`:

| File | Import into |
|---|---|
| `<Solution>_<version>_managed.zip` | Test, then the **same file** into Production |
| `<Solution>_<version>.zip` (unmanaged) | Dev only, to open the app in Studio from the solution (PA-T8) |

The importer chooses environment variable values and connections in the portal's import wizard: the ZIPs carry none
(PA-T4), which is why they are safe to commit. The steps are in the release notes and the
[README](../README.md#importing). Record each import into Test or Production in PROJECT.md §7, citing the file here.

Never overwrite or hand-edit a file here. A fix is a new version, built by `/verify release`. `dist/` stays the build
output and is ignored.
