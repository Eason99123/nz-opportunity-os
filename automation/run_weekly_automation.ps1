param(
    [ValidateSet(
        "",
        "openclaw_search",
        "clean",
        "validation",
        "append",
        "lifecycle",
        "refresh",
        "batch_status",
        "health"
    )]
    [string]$TestFailureStage = ""
)


$ErrorActionPreference = "Stop"


# ============================================================
# NZ Student Opportunity OS
# Weekly Production Automation
#
# Pipeline
#
# OpenClaw
# -> Raw
# -> Clean
# -> Validate
# -> Approved only
# -> Append Batch
# -> Lifecycle
# -> Active only Production Batch
# -> Refresh Live
# -> Update Batch Status
# -> Save Weekly Status
# -> Update Automation Health
#
# Failure protection
#
# Transaction Backup
# -> Production modification
# -> Failure
# -> Restore Production Batch
# -> Restore Live
# -> Restore Batch Status
# -> Record rollback
# ============================================================


$ProjectRoot = Split-Path -Parent $PSScriptRoot

$IncomingDir = Join-Path `
    $ProjectRoot `
    "incoming"

$LogsDir = Join-Path `
    $ProjectRoot `
    "logs"


# ============================================================
# Input files
# ============================================================

$RawFile = Join-Path `
    $IncomingDir `
    "openclaw_raw.txt"

$CleanedFile = Join-Path `
    $IncomingDir `
    "openclaw_cleaned.txt"

$ApprovedFile = Join-Path `
    $IncomingDir `
    "openclaw_approved.txt"

$ReviewFile = Join-Path `
    $IncomingDir `
    "openclaw_needs_review.txt"

$RejectedFile = Join-Path `
    $IncomingDir `
    "openclaw_rejected.txt"

$CleanedBackupFile = Join-Path `
    $IncomingDir `
    "openclaw_cleaned_pre_publish_backup.txt"


# ============================================================
# Production files
# ============================================================

$BatchFile = Join-Path `
    $IncomingDir `
    "openclaw_batch.txt"

$ActiveFile = Join-Path `
    $IncomingDir `
    "openclaw_active.txt"

$LifecycleReviewFile = Join-Path `
    $IncomingDir `
    "openclaw_lifecycle_review.txt"


# ============================================================
# Prompt
# ============================================================

$PromptFile = Join-Path `
    $PSScriptRoot `
    "weekly_prompt.txt"


# ============================================================
# Python scripts
# ============================================================

$CleanScript = Join-Path `
    $ProjectRoot `
    "src\clean_openclaw_output.py"

$ValidatorScript = Join-Path `
    $ProjectRoot `
    "src\validate_opportunities.py"

$AppendScript = Join-Path `
    $ProjectRoot `
    "src\append_openclaw_batch.py"

$LifecycleScript = Join-Path `
    $ProjectRoot `
    "src\archive_expired_opportunities.py"

$RefreshScript = Join-Path `
    $ProjectRoot `
    "src\refresh_from_batch.py"

$BatchStatusScript = Join-Path `
    $ProjectRoot `
    "src\write_batch_status.py"

$HealthScript = Join-Path `
    $ProjectRoot `
    "src\write_automation_health.py"


# ============================================================
# Logs and status
# ============================================================

$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

$LogFile = Join-Path `
    $LogsDir `
    "weekly_automation_$Timestamp.log"

$LatestLogFile = Join-Path `
    $LogsDir `
    "latest_weekly_automation.log"

$StatusFile = Join-Path `
    $LogsDir `
    "latest_weekly_automation_status.json"

$LatestSuccessfulRunFile = Join-Path `
    $LogsDir `
    "latest_successful_weekly_run.json"

$ValidationStatusFile = Join-Path `
    $LogsDir `
    "latest_validation_status.json"

$LifecycleStatusFile = Join-Path `
    $LogsDir `
    "latest_archive_status.json"

$HealthStatusFile = Join-Path `
    $LogsDir `
    "latest_automation_health.json"

$AgentErrorFile = Join-Path `
    $LogsDir `
    "openclaw_agent_error_$Timestamp.log"


# ============================================================
# Runtime
# ============================================================

$StartedAt = Get-Date

$Utf8NoBom = New-Object `
    System.Text.UTF8Encoding($false)


# ============================================================
# Transaction state
# ============================================================

$FailureStage = "startup"

$RollbackPerformed = $false

$ProductionModified = $false

$TransactionBackupFile = $null

$LifecycleBackupFile = $null


# ============================================================
# Counters
# ============================================================

$ApprovedCount = 0
$ReviewCount = 0
$RejectedCount = 0
$TotalCount = 0

$LifecycleTotal = 0
$LifecycleActive = 0
$LifecycleUncertain = 0
$LifecycleExpired = 0


# ============================================================
# Ensure directories
# ============================================================

New-Item `
    -ItemType Directory `
    -Force `
    -Path $IncomingDir |
    Out-Null

New-Item `
    -ItemType Directory `
    -Force `
    -Path $LogsDir |
    Out-Null


# ============================================================
# Helper functions
# ============================================================

function Write-Log {

    param(
        [string]$Message
    )

    $Line = "[{0}] {1}" -f `
        (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), `
        $Message

    Write-Host $Line

    Add-Content `
        -Path $LogFile `
        -Value $Line `
        -Encoding UTF8
}


function Get-ValidationSummary {

    if (-not (Test-Path $ValidationStatusFile)) {
        return $null
    }

    try {
        return (
            Get-Content `
                $ValidationStatusFile `
                -Raw |
            ConvertFrom-Json
        )
    }
    catch {
        return $null
    }
}


function Get-LifecycleSummary {

    if (-not (Test-Path $LifecycleStatusFile)) {
        return $null
    }

    try {
        return (
            Get-Content `
                $LifecycleStatusFile `
                -Raw |
            ConvertFrom-Json
        )
    }
    catch {
        return $null
    }
}


function Save-Status {

    param(
        [string]$Status,
        [string]$Message
    )

    $Validation = Get-ValidationSummary
    $Lifecycle = Get-LifecycleSummary

    $DurationSeconds = [math]::Round(
        (
            (Get-Date) - $StartedAt
        ).TotalSeconds,
        2
    )

    $StatusObject = [ordered]@{

        status = $Status

        message = $Message

        started_at = $StartedAt.ToString(
            "yyyy-MM-dd HH:mm:ss"
        )

        finished_at = (Get-Date).ToString(
            "yyyy-MM-dd HH:mm:ss"
        )

        duration_seconds = $DurationSeconds

        failure_stage = $FailureStage

        rollback_performed = $RollbackPerformed

        production_modified = $ProductionModified

        test_failure_stage = $TestFailureStage

        transaction_backup_file = $TransactionBackupFile

        lifecycle_backup_file = $LifecycleBackupFile

        log_file = $LogFile

        raw_file = $RawFile

        cleaned_file = $CleanedFile

        approved_file = $ApprovedFile

        needs_review_file = $ReviewFile

        rejected_file = $RejectedFile

        production_batch_file = $BatchFile

        lifecycle_review_file = $LifecycleReviewFile

        automation_health_file = $HealthStatusFile
    }

    if ($null -ne $Validation) {

        $StatusObject["validation"] = [ordered]@{

            total_entries = $Validation.total_entries

            approved = $Validation.approved

            needs_review = $Validation.needs_review

            rejected = $Validation.rejected
        }
    }

    if ($null -ne $Lifecycle) {

        $StatusObject["lifecycle"] = [ordered]@{

            total_entries = $Lifecycle.total_entries

            active = $Lifecycle.active

            uncertain = $Lifecycle.uncertain

            expired = $Lifecycle.expired
        }
    }

    $Json = $StatusObject |
        ConvertTo-Json -Depth 8

    [System.IO.File]::WriteAllText(
        $StatusFile,
        $Json,
        $Utf8NoBom
    )
}


function Invoke-TestFailure {

    param(
        [string]$Stage
    )

    if (
        -not [string]::IsNullOrWhiteSpace(
            $TestFailureStage
        )
    ) {

        if ($TestFailureStage -eq $Stage) {

            Write-Log (
                "TEST FAILURE INJECTION triggered at stage: $Stage"
            )

            throw (
                "Injected test failure at stage: $Stage"
            )
        }
    }
}


function Run-PythonScript {

    param(
        [string]$Description,
        [string[]]$Arguments
    )

    Write-Log $Description

    & python @Arguments

    if ($LASTEXITCODE -ne 0) {

        throw (
            "$Description failed with exit code " +
            "$LASTEXITCODE."
        )
    }
}


# ============================================================
# Main pipeline
# ============================================================

try {

    Set-Location $ProjectRoot


    $FailureStage = "startup"

    Write-Log (
        "NZ Opportunity OS weekly automation started."
    )

    Write-Log (
        "Project root: $ProjectRoot"
    )


    if (
        -not [string]::IsNullOrWhiteSpace(
            $TestFailureStage
        )
    ) {

        Write-Log (
            "TEST MODE ENABLED. Failure stage: $TestFailureStage"
        )
    }


    # ========================================================
    # Required files
    # ========================================================

    $FailureStage = "required_files"

    $RequiredFiles = @(
        $PromptFile,
        $CleanScript,
        $ValidatorScript,
        $AppendScript,
        $LifecycleScript,
        $RefreshScript,
        $BatchStatusScript,
        $HealthScript
    )

    foreach ($File in $RequiredFiles) {

        if (-not (Test-Path $File)) {

            throw (
                "Required file not found: $File"
            )
        }
    }


    # ========================================================
    # Gateway
    # ========================================================

    $FailureStage = "gateway"

    Write-Log (
        "Checking OpenClaw Gateway."
    )

    & openclaw gateway status --deep |
        Out-Null

    if ($LASTEXITCODE -ne 0) {

        Write-Log (
            "Gateway check failed. Attempting restart."
        )

        & openclaw gateway restart |
            Out-Null

        Start-Sleep -Seconds 8

        & openclaw gateway status --deep |
            Out-Null

        if ($LASTEXITCODE -ne 0) {

            throw (
                "OpenClaw Gateway is unavailable after restart."
            )
        }
    }

    Write-Log (
        "Gateway is available."
    )


    # ========================================================
    # Transaction backup
    # ========================================================

    $FailureStage = "transaction_backup"

    $TransactionBackupDir = Join-Path `
        $ProjectRoot `
        "opportunities\transaction_backups"

    New-Item `
        -ItemType Directory `
        -Force `
        -Path $TransactionBackupDir |
        Out-Null

    if (Test-Path $BatchFile) {

        $TransactionBackupFile = Join-Path `
            $TransactionBackupDir `
            (
                "openclaw_batch_before_weekly_run_" +
                (Get-Date -Format "yyyy-MM-dd_HHmmss") +
                ".txt"
            )

        Copy-Item `
            $BatchFile `
            $TransactionBackupFile `
            -Force

        Write-Log (
            "Transaction backup created: $TransactionBackupFile"
        )
    }
    else {

        Write-Log (
            "No existing production batch found before transaction."
        )
    }


    # ========================================================
    # OpenClaw
    # ========================================================

    $FailureStage = "openclaw_search"

    Invoke-TestFailure `
        -Stage "openclaw_search"

    Write-Log (
        "Starting opportunity search."
    )

    $SessionKey = (
        "nz-opportunity-weekly-auto-{0}" -f
        (Get-Date -Format "yyyyMMdd-HHmmss")
    )

    Write-Log (
        "Using fresh session: $SessionKey"
    )

    Remove-Item `
        $AgentErrorFile `
        -Force `
        -ErrorAction SilentlyContinue

    $PreviousErrorActionPreference = $ErrorActionPreference

    try {

        $ErrorActionPreference = "Continue"

        $AgentOutput = & openclaw agent `
            --agent main `
            --session-key $SessionKey `
            --message-file $PromptFile `
            --thinking minimal `
            --timeout 900 `
            2> $AgentErrorFile

        $AgentExitCode = $LASTEXITCODE
    }
    finally {

        $ErrorActionPreference = $PreviousErrorActionPreference
    }

    if ($AgentExitCode -ne 0) {

        throw (
            "OpenClaw agent failed with exit code " +
            "$AgentExitCode. See $AgentErrorFile"
        )
    }

    if (Test-Path $AgentErrorFile) {

        $AgentWarnings = Get-Content `
            $AgentErrorFile `
            -Raw

        if (
            -not [string]::IsNullOrWhiteSpace(
                $AgentWarnings
            )
        ) {

            Write-Log (
                "OpenClaw emitted warnings. See: " +
                "$AgentErrorFile"
            )
        }
    }


    # ========================================================
    # Normalize output
    # ========================================================

    $FailureStage = "normalize"

    $FullAgentText = (
        $AgentOutput -join [Environment]::NewLine
    ).Trim()

    if (
        [string]::IsNullOrWhiteSpace(
            $FullAgentText
        )
    ) {

        throw (
            "OpenClaw returned an empty response."
        )
    }

    if (
        $FullAgentText -match "The agent run failed" -or
        $FullAgentText -match "I am encountering an issue" -or
        $FullAgentText -match "All models failed" -or
        $FullAgentText -match "ECONNREFUSED"
    ) {

        throw (
            "OpenClaw returned an error response instead of opportunity data."
        )
    }

    if (
        $FullAgentText -match "(?m)^NO_STRONG_MATCHES\s*$"
    ) {

        $RawText = "NO_STRONG_MATCHES"
    }
    else {

        $TitleMatch = [regex]::Match(
            $FullAgentText,
            "(?m)^Title:\s*.+$"
        )

        if (-not $TitleMatch.Success) {

            [System.IO.File]::WriteAllText(
                $RawFile,
                $FullAgentText,
                $Utf8NoBom
            )

            throw (
                "No Title field was found in the OpenClaw response."
            )
        }

        $RawText = $FullAgentText.Substring(
            $TitleMatch.Index
        ).Trim()

        $TrailingSectionMatch = [regex]::Match(
            $RawText,
            (
                "(?m)^(" +
                "Next \d+ actions:|" +
                "What to save to memory:|" +
                "Summary:|" +
                "Recommendations:" +
                ")"
            )
        )

        if ($TrailingSectionMatch.Success) {

            $RawText = $RawText.Substring(
                0,
                $TrailingSectionMatch.Index
            ).Trim()
        }
    }

    [System.IO.File]::WriteAllText(
        $RawFile,
        $RawText,
        $Utf8NoBom
    )

    Write-Log (
        "Raw output normalized and saved using UTF-8."
    )

    Write-Log (
        "Normalized output length: $($RawText.Length) characters."
    )

    $HasNewMatches = $true

    if ($RawText -eq "NO_STRONG_MATCHES") {

        $HasNewMatches = $false

        Write-Log (
            "No strong new opportunities were found."
        )
    }

    if (
        $HasNewMatches -and
        -not $RawText.StartsWith("Title:")
    ) {

        throw (
            "Unexpected OpenClaw output format."
        )
    }


    # ========================================================
    # Clean, validate, append
    # ========================================================

    if ($HasNewMatches) {

        $FailureStage = "clean"

        Invoke-TestFailure `
            -Stage "clean"

        Run-PythonScript `
            -Description "Cleaning OpenClaw output." `
            -Arguments @(
                $CleanScript,
                $RawFile,
                $CleanedFile
            )

        if (-not (Test-Path $CleanedFile)) {

            throw (
                "The cleaned output file was not created."
            )
        }

        $CleanedText = Get-Content `
            $CleanedFile `
            -Raw

        if (
            [string]::IsNullOrWhiteSpace(
                $CleanedText
            )
        ) {

            throw (
                "The cleaned output file is empty."
            )
        }

        if (
            -not $CleanedText.TrimStart().StartsWith(
                "Title:"
            )
        ) {

            throw (
                "The cleaned output does not start with Title:."
            )
        }

        Write-Log (
            "Cleaned opportunity data is valid."
        )


        # Validation

        $FailureStage = "validation"

        Invoke-TestFailure `
            -Stage "validation"

        Run-PythonScript `
            -Description "Validating cleaned opportunities." `
            -Arguments @(
                $ValidatorScript,
                $CleanedFile
            )

        if (
            -not (Test-Path $ValidationStatusFile)
        ) {

            throw (
                "Validation status file was not created."
            )
        }

        try {

            $ValidationStatus = (
                Get-Content `
                    $ValidationStatusFile `
                    -Raw |
                ConvertFrom-Json
            )
        }
        catch {

            throw (
                "Validation status JSON could not be parsed."
            )
        }

        if (
            $ValidationStatus.status -ne "success"
        ) {

            throw (
                "Validator did not report success."
            )
        }

        $ApprovedCount = [int](
            $ValidationStatus.approved
        )

        $ReviewCount = [int](
            $ValidationStatus.needs_review
        )

        $RejectedCount = [int](
            $ValidationStatus.rejected
        )

        $TotalCount = [int](
            $ValidationStatus.total_entries
        )

        Write-Log (
            "Validation completed: " +
            "$ApprovedCount approved, " +
            "$ReviewCount needs review, " +
            "$RejectedCount rejected " +
            "out of $TotalCount."
        )


        # Approved only append

        if ($ApprovedCount -gt 0) {

            if (-not (Test-Path $ApprovedFile)) {

                throw (
                    "Approved opportunities file is missing."
                )
            }

            $ApprovedText = Get-Content `
                $ApprovedFile `
                -Raw

            if (
                [string]::IsNullOrWhiteSpace(
                    $ApprovedText
                )
            ) {

                throw (
                    "Approved count is greater than zero, but approved file is empty."
                )
            }

            Write-Log (
                "Preparing approved-only publishing input."
            )

            Remove-Item `
                $CleanedBackupFile `
                -Force `
                -ErrorAction SilentlyContinue

            Copy-Item `
                $CleanedFile `
                $CleanedBackupFile `
                -Force

            try {

                Copy-Item `
                    $ApprovedFile `
                    $CleanedFile `
                    -Force

                Write-Log (
                    "Publishing approved opportunities only."
                )

                $ProductionModified = $true

                $FailureStage = "append"

                Invoke-TestFailure `
                    -Stage "append"

                Run-PythonScript `
                    -Description "Appending approved opportunities to batch." `
                    -Arguments @(
                        $AppendScript
                    )
            }
            finally {

                if (
                    Test-Path $CleanedBackupFile
                ) {

                    Copy-Item `
                        $CleanedBackupFile `
                        $CleanedFile `
                        -Force

                    Remove-Item `
                        $CleanedBackupFile `
                        -Force `
                        -ErrorAction SilentlyContinue

                    Write-Log (
                        "Original cleaned output restored."
                    )
                }
            }
        }
        else {

            Write-Log (
                "No new opportunities passed validation."
            )
        }
    }


    # ========================================================
    # Lifecycle
    # ========================================================

    $FailureStage = "lifecycle"

    Invoke-TestFailure `
        -Stage "lifecycle"

    Write-Log (
        "Running lifecycle check on production batch."
    )

    if (-not (Test-Path $BatchFile)) {

        throw (
            "Production batch file does not exist before lifecycle check."
        )
    }

    $LifecycleBackupDir = Join-Path `
        $ProjectRoot `
        "opportunities\lifecycle_backups"

    New-Item `
        -ItemType Directory `
        -Force `
        -Path $LifecycleBackupDir |
        Out-Null

    $LifecycleBackupFile = Join-Path `
        $LifecycleBackupDir `
        (
            "openclaw_batch_before_lifecycle_" +
            (Get-Date -Format "yyyy-MM-dd_HHmmss") +
            ".txt"
        )

    Copy-Item `
        $BatchFile `
        $LifecycleBackupFile `
        -Force

    Write-Log (
        "Lifecycle backup created: $LifecycleBackupFile"
    )

    Run-PythonScript `
        -Description "Classifying opportunity lifecycle." `
        -Arguments @(
            $LifecycleScript,
            $BatchFile
        )

    if (
        -not (Test-Path $LifecycleStatusFile)
    ) {

        throw (
            "Lifecycle status JSON was not created."
        )
    }

    try {

        $LifecycleStatus = (
            Get-Content `
                $LifecycleStatusFile `
                -Raw |
            ConvertFrom-Json
        )
    }
    catch {

        throw (
            "Lifecycle status JSON could not be parsed."
        )
    }

    if (
        $LifecycleStatus.status -ne "success"
    ) {

        throw (
            "Lifecycle classifier did not report success."
        )
    }

    $LifecycleTotal = [int](
        $LifecycleStatus.total_entries
    )

    $LifecycleActive = [int](
        $LifecycleStatus.active
    )

    $LifecycleUncertain = [int](
        $LifecycleStatus.uncertain
    )

    $LifecycleExpired = [int](
        $LifecycleStatus.expired
    )

    Write-Log (
        "Lifecycle completed: " +
        "$LifecycleActive active, " +
        "$LifecycleUncertain uncertain, " +
        "$LifecycleExpired expired " +
        "out of $LifecycleTotal."
    )

    if (
        (
            $LifecycleActive +
            $LifecycleUncertain +
            $LifecycleExpired
        ) -ne $LifecycleTotal
    ) {

        throw (
            "Lifecycle counts do not add up to total entries."
        )
    }


    # ========================================================
    # Production policy
    # ========================================================

    $ProductionModified = $true

    if ($LifecycleActive -eq 0) {

        [System.IO.File]::WriteAllText(
            $BatchFile,
            "",
            $Utf8NoBom
        )
    }
    else {

        if (
            -not (Test-Path $ActiveFile)
        ) {

            throw (
                "Lifecycle reported active entries but active output file is missing."
            )
        }

        Copy-Item `
            $ActiveFile `
            $BatchFile `
            -Force
    }

    Write-Log (
        "Production batch compacted to active opportunities only."
    )


    # ========================================================
    # Refresh
    # ========================================================

    $FailureStage = "refresh"

    Invoke-TestFailure `
        -Stage "refresh"

    Run-PythonScript `
        -Description "Refreshing live data from batch." `
        -Arguments @(
            $RefreshScript
        )


    # ========================================================
    # Batch status
    # ========================================================

    $FailureStage = "batch_status"

    Invoke-TestFailure `
        -Stage "batch_status"

    Run-PythonScript `
        -Description "Updating batch status." `
        -Arguments @(
            $BatchStatusScript
        )


    # ========================================================
    # Current weekly status before health
    # ========================================================

    $FailureStage = "weekly_status"

    Save-Status `
        -Status "success" `
        -Message (
            "$ApprovedCount new opportunities were approved. " +
            "$ReviewCount require validation review. " +
            "$RejectedCount were rejected. " +
            "$LifecycleActive opportunities remain active. " +
            "$LifecycleExpired expired opportunities were archived. " +
            "$LifecycleUncertain require lifecycle review."
        )


    # ========================================================
    # Health
    # ========================================================

    $FailureStage = "health"

    Invoke-TestFailure `
        -Stage "health"

    Run-PythonScript `
        -Description "Updating automation health status." `
        -Arguments @(
            $HealthScript
        )


    # ========================================================
    # Commit
    # ========================================================

    $FailureStage = "completed"

    Write-Log (
        "Transaction committed successfully."
    )

    Save-Status `
        -Status "success" `
        -Message (
            "$ApprovedCount new opportunities were approved. " +
            "$ReviewCount require validation review. " +
            "$RejectedCount were rejected. " +
            "$LifecycleActive opportunities remain active. " +
            "$LifecycleExpired expired opportunities were archived. " +
            "$LifecycleUncertain require lifecycle review."
        )

    Copy-Item `
        $StatusFile `
        $LatestSuccessfulRunFile `
        -Force

    Write-Log (
        "Latest successful run snapshot updated."
    )

    Write-Log (
        "Weekly validated lifecycle automation completed successfully."
    )

    Copy-Item `
        $LogFile `
        $LatestLogFile `
        -Force

    exit 0
}
catch {

    $ErrorMessage = $_.Exception.Message

    Write-Log (
        "Failure detected at stage: $FailureStage"
    )

    if (
        Test-Path $CleanedBackupFile
    ) {

        try {

            Copy-Item `
                $CleanedBackupFile `
                $CleanedFile `
                -Force

            Remove-Item `
                $CleanedBackupFile `
                -Force `
                -ErrorAction SilentlyContinue
        }
        catch {
        }
    }


    # ========================================================
    # Rollback
    # ========================================================

    if (
        $ProductionModified -and
        $null -ne $TransactionBackupFile -and
        (Test-Path $TransactionBackupFile)
    ) {

        try {

            Write-Log (
                "Attempting production rollback."
            )

            Copy-Item `
                $TransactionBackupFile `
                $BatchFile `
                -Force

            $RollbackPerformed = $true

            Write-Log (
                "Production batch restored from transaction backup."
            )

            try {

                Write-Log (
                    "Refreshing live data after rollback."
                )

                & python $RefreshScript

                if ($LASTEXITCODE -ne 0) {

                    throw (
                        "Rollback refresh failed."
                    )
                }

                Write-Log (
                    "Live data restored after rollback."
                )
            }
            catch {

                Write-Log (
                    "WARNING: live refresh after rollback failed."
                )
            }

            try {

                & python $BatchStatusScript

                if ($LASTEXITCODE -ne 0) {

                    throw (
                        "Rollback batch status update failed."
                    )
                }

                Write-Log (
                    "Batch status restored after rollback."
                )
            }
            catch {

                Write-Log (
                    "WARNING: batch status after rollback failed."
                )
            }
        }
        catch {

            Write-Log (
                "CRITICAL: automatic rollback failed: " +
                $_.Exception.Message
            )
        }
    }
    else {

        Write-Log (
            "Rollback was not required because production was not modified."
        )
    }


    Write-Log (
        "AUTOMATION FAILED: $ErrorMessage"
    )

    Save-Status `
        -Status "failed" `
        -Message $ErrorMessage


    try {

        Write-Log (
            "Updating automation health after failure."
        )

        & python $HealthScript
    }
    catch {

        Write-Log (
            "WARNING: automation health could not be updated after failure."
        )
    }

    Copy-Item `
        $LogFile `
        $LatestLogFile `
        -Force

    exit 1
}