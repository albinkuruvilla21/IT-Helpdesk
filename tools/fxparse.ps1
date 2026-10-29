<#
fxparse.ps1: parses Power Fx formulas with Microsoft's own parser (Microsoft.PowerFx.Core, shipped inside the Power Platform CLI).

Called by tools/powerfx.py; not meant to be run by hand. Needs PowerShell 7 on the same .NET major version as pac (pac 2.13 = .NET 10,
PowerShell 7.6). Parse only: Microsoft's parser decides whether a formula is well formed; it does not know the app's controls, lists or
variables, so it does not bind names. That is done, more loosely, by powerfx.py, and finally by Power Apps Studio.

  -Dll <path to Microsoft.PowerFx.Core.dll> -In <formulas.json> -Out <results.json>
      In:  [{"id": "...", "text": "...", "behavior": true|false}, ...]
      Out: {"version": "1.99.0.0", "results": [{"id": "...", "ok": true|false, "errors": [{"message": "...", "start": 0, "end": 0}]}]}
  -Dll <path> -DumpFunctions -Out <functions.json>
      The engine's function library with min/max arity (Core, plus the Interpreter's mutation functions when that DLL is beside it).
#>
param(
    [Parameter(Mandatory = $true)][string]$Dll,
    [string]$In,
    [Parameter(Mandatory = $true)][string]$Out,
    [switch]$DumpFunctions
)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $Dll
$attrs = Join-Path $dir 'Microsoft.PowerFx.Transport.Attributes.dll'
if (Test-Path $attrs) { [void][Reflection.Assembly]::LoadFrom($attrs) }
$asm = [Reflection.Assembly]::LoadFrom($Dll)
$version = $asm.GetName().Version.ToString()

if ($DumpFunctions) {
    $cfg = [Microsoft.PowerFx.PowerFxConfig]::new()
    $interp = Join-Path $dir 'Microsoft.PowerFx.Interpreter.dll'
    $sources = @('Microsoft.PowerFx.Core')
    if (Test-Path $interp) {
        [void][Reflection.Assembly]::LoadFrom($interp)
        # Set, Patch, Collect, Remove, ClearCollect ... are registered by the Interpreter, not by Core.
        [Microsoft.PowerFx.PowerFxConfigExtensions]::EnableSetFunction($cfg)
        [Microsoft.PowerFx.PowerFxConfigExtensions]::EnableMutationFunctions($cfg.SymbolTable)
        $sources += 'Microsoft.PowerFx.Interpreter (EnableSetFunction, EnableMutationFunctions)'
    }
    $byName = @{}
    foreach ($f in $cfg.FunctionInfos) {
        $n = $f.Name
        if (-not $byName.ContainsKey($n)) { $byName[$n] = @{ name = $n; min = [int]$f.MinArity; max = [int]$f.MaxArity } }
        else {
            $e = $byName[$n]
            $e.min = [Math]::Min($e.min, [int]$f.MinArity)
            $e.max = [Math]::Max($e.max, [int]$f.MaxArity)
        }
    }
    $list = $byName.Values | Sort-Object { $_.name } | ForEach-Object {
        [ordered]@{ name = $_.name; min = $_.min; max = $(if ($_.max -ge [int]::MaxValue) { $null } else { $_.max }) }
    }
    [ordered]@{ version = $version; sources = $sources; functions = @($list) } | ConvertTo-Json -Depth 5 | Set-Content -Path $Out -Encoding utf8
    exit 0
}

$items = Get-Content -Raw -Path $In -Encoding utf8 | ConvertFrom-Json
$results = foreach ($it in @($items)) {
    $opts = [Microsoft.PowerFx.ParserOptions]::new()
    $opts.AllowsSideEffects = [bool]$it.behavior
    $r = [Microsoft.PowerFx.Engine]::Parse([string]$it.text, $null, $opts)
    $errs = @($r.Errors | ForEach-Object { [ordered]@{ message = $_.Message; start = $_.Span.Min; end = $_.Span.Lim } })
    [ordered]@{ id = $it.id; ok = [bool]$r.IsSuccess; errors = $errs }
}
[ordered]@{ version = $version; results = @($results) } | ConvertTo-Json -Depth 6 | Set-Content -Path $Out -Encoding utf8
