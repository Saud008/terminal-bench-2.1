param(
    [Parameter(Mandatory = $true)]
    [string]$TaskName,
    [switch]$Milestone
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$TaskDir = Join-Path (Join-Path $Root "tasks") $TaskName
$OutDir = Join-Path $Root "tasksubmit"

$OutZip = Join-Path $OutDir "$TaskName.zip"

if (-not (Test-Path $TaskDir)) {
    Write-Error "Task not found: $TaskDir"
}

if ($Milestone) {
    $required = @("task.toml", "environment", "steps")
} else {
    $required = @("instruction.md", "task.toml", "environment", "tests", "solution")
}

foreach ($r in $required) {
    if (-not (Test-Path (Join-Path $TaskDir $r))) {
        Write-Error "Missing required: $r in $TaskDir"
    }
}

$Dockerfile = Join-Path $TaskDir "environment\Dockerfile"
if (Test-Path $Dockerfile) {
    $python = $null
    foreach ($cmd in @("python3", "python")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $python = $cmd
            break
        }
    }
    if ($python) {
        & $python "$Root\scripts\migrate_dockerfile_canonical_ecr.py" --ensure --quiet --task-dir $TaskDir
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Canonical ECR FROM required before zip (see canonical-base-image-gate.mdc)"
        }
        & $python "$Root\scripts\ensure_subcategories_empty.py" --ensure --quiet --task-dir $TaskDir
        if ($LASTEXITCODE -ne 0) {
            Write-Error "task.toml must have subcategories = [] (see task-toml-subcategories-gate.mdc)"
        }
        if ($env:TERMINUS_TASK_TOML_FIELDS_SKIP -ne "1") {
            & $python "$Root\scripts\ensure_task_toml_supported_fields.py" --check --quiet --task-dir $TaskDir
            if ($LASTEXITCODE -ne 0) {
                Write-Error "task.toml has unsupported/undocumented fields (see task-toml-supported-fields-only.mdc). Override: `$env:TERMINUS_TASK_TOML_FIELDS_SKIP='1'"
            }
        }
        if ($env:TERMINUS_ANTI_SPAM_SKIP -ne "1") {
            $spamArgs = @("pack", "--task-name", $TaskName)
            if ($env:TERMINUS_ANTI_SPAM_STRICT_REPO -eq "1") {
                $spamArgs += "--strict-repo"
            }
            & $python "$Root\scripts\terminus_anti_spam_auto.py" @spamArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Anti-spam/templated gate failed (see anti-spam-templated-submissions.mdc). Details: jobs-local/anti-spam-last.txt. Override: `$env:TERMINUS_ANTI_SPAM_SKIP='1'"
            }
        }
        if ($env:TERMINUS_FIRST_SUBMIT_SKIP -ne "1") {
            & $python "$Root\scripts\first_submit_pack_gate.py" --pack-gate --quiet --task-dir $TaskDir
            if ($LASTEXITCODE -ne 0) {
                Write-Error "First-submit gate failed (Phase F'). No zip created. Record PASS: python3 scripts/first_submit_pack_gate.py --record --task-dir tasks/$TaskName ... Details: jobs-local/first-submit-last.txt. Override: `$env:TERMINUS_FIRST_SUBMIT_SKIP='1'"
            }
        }
    }
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (Test-Path $OutZip) { Remove-Item $OutZip -Force }

$zipExcludes = @(
    "**/.pytest_cache/*", "**/.ruff_cache/*", "output/*", "jobs/**",
    "**/__pycache__/*", "**/*.pyc", "environment/target/*",
    "environment/app/build/*", "**/node_modules/*",
    "rubric.md", "**/rubric.md"
)

function Test-ZipLayout {
    param([string]$ZipPath, [string]$Name, [bool]$IsMilestone)
    $v = Join-Path $env:TEMP "zip_check_$([guid]::NewGuid().ToString('N'))"
    New-Item -ItemType Directory -Path $v -Force | Out-Null
    try {
        tar -xf $ZipPath -C $v 2>$null
        if (-not $?) {
            Expand-Archive -Path $ZipPath -DestinationPath $v -Force
        }
        if ($IsMilestone) {
            if (-not (Test-Path (Join-Path $v "task.toml")) -or -not (Test-Path (Join-Path $v "steps"))) {
                throw "Bad milestone layout in zip"
            }
        } else {
            foreach ($p in @("task.toml", "tests\test.sh", "tests\test_outputs.py", "environment\Dockerfile")) {
                if (-not (Test-Path (Join-Path $v ($p -replace '/', '\')))) {
                    throw "Missing at zip root: $p"
                }
            }
        }
        if (Test-Path (Join-Path $v $Name)) {
            throw "Nested folder $Name/ in zip (flat root required)"
        }
        if (Get-ChildItem -Path $v -Recurse -Filter "rubric.md" -ErrorAction SilentlyContinue) {
            throw "rubric.md must not be in zip"
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
        try {
            $bad = @($zip.Entries | Where-Object { $_.FullName -match '\\' })
            if ($bad.Count -gt 0) {
                throw "Backslash paths in zip (G-027): $($bad[0].FullName)"
            }
        } finally {
            $zip.Dispose()
        }
    } finally {
        Remove-Item $v -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Push-Location $TaskDir
try {
    $wslTask = ($TaskDir -replace '\\', '/') -replace '^C:', '/mnt/c'
    $wslZip = ($OutZip -replace '\\', '/') -replace '^C:', '/mnt/c'
    $excludeArgs = ($zipExcludes | ForEach-Object { "-x `"$_`"" }) -join ' '
    $hasWsl = Get-Command wsl -ErrorAction SilentlyContinue

    if ($hasWsl) {
        wsl bash -lc "cd '$wslTask' && zip -r '$wslZip' . $excludeArgs"
    } elseif (Get-Command tar -ErrorAction SilentlyContinue) {
        $tarExcludes = @(
            "--exclude=.pytest_cache", "--exclude=.ruff_cache", "--exclude=output", "--exclude=jobs",
            "--exclude=**/__pycache__", "--exclude=rubric.md"
        )
        if ($Milestone) {
            & tar -a -cf $OutZip @tarExcludes task.toml environment steps
        } else {
            & tar -a -cf $OutZip @tarExcludes instruction.md task.toml environment tests solution
        }
    } else {
        Write-Error "Need WSL zip or tar. Do not use Compress-Archive (G-027 backslash paths). Install Git/WSL or use Mac: scripts/pack_zip.sh"
    }
} finally {
    Pop-Location
}

Test-ZipLayout -ZipPath $OutZip -Name $TaskName -IsMilestone $Milestone.IsPresent

Write-Host "Wrote: $OutZip"
Write-Host ("Size: {0:N0} bytes" -f (Get-Item $OutZip).Length)

if ($python) {
    & $python "$Root\scripts\terminus_anti_spam_check.py" --register-pack --quiet --task-name $TaskName
}
