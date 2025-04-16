# PowerShell script to register all commands in the user's profile
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScriptsPath = Join-Path $scriptPath "scripts"

# Create the profile if it doesn't exist
if (!(Test-Path -Path $PROFILE)) {
    Write-Host "PowerShell profile does not exist. Creating it..." -ForegroundColor Yellow
    New-Item -ItemType File -Path $PROFILE -Force
    Write-Host "Created PowerShell profile at $PROFILE" -ForegroundColor Green
}

# Get all Python scripts in the scripts directory
$pythonScripts = Get-ChildItem -Path $pythonScriptsPath -Filter "*.py"
Write-Host "Found the following scripts to install:" -ForegroundColor Cyan
foreach ($script in $pythonScripts) {
    Write-Host " - $($script.BaseName.Replace("_", "-"))" -ForegroundColor Cyan
}

# Check if any of the commands are already in the profile
$profileContent = Get-Content -Path $PROFILE -ErrorAction SilentlyContinue
$commandsToAdd = @()

foreach ($script in $pythonScripts) {
    $commandName = $script.BaseName.Replace("_", "-")
    $fullPath = $script.FullName.Replace("\", "/")  # Convert to forward slashes for PowerShell
    
    # Check if command is already in profile
    if ($profileContent -match "function $commandName") {
        Write-Host "Command '$commandName' already exists in profile. Skipping..." -ForegroundColor Yellow
    } else {
        $commandsToAdd += @{
            Name = $commandName
            Path = $fullPath
        }
    }
}

# Add the new commands to the profile
if ($commandsToAdd.Count -gt 0) {
    Write-Host "Adding the following commands to your PowerShell profile:" -ForegroundColor Green
    
    $newCommands = ""
    foreach ($command in $commandsToAdd) {
        Write-Host " - $($command.Name)" -ForegroundColor Green
        $newCommands += @"
function $($command.Name) {
    & python "$($command.Path)" @args
}

"@
    }
    
    Add-Content -Path $PROFILE -Value $newCommands
    Write-Host "Commands have been added to your PowerShell profile at $PROFILE" -ForegroundColor Green
    Write-Host "Please restart your PowerShell session or run 'Import-Module $PROFILE' to use the new commands" -ForegroundColor Yellow
} else {
    Write-Host "No new commands to add to profile." -ForegroundColor Yellow
}

# Create uninstall script
$uninstallContent = @"
# uninstall_windows.ps1
# Script to remove the installed commands from PowerShell profile

# Commands to remove
`$commandsToRemove = [System.Collections.ArrayList]@(
$(foreach ($script in $pythonScripts) {
    "    '$($script.BaseName.Replace("_", "-"))'`r`n"
}))

# Get profile content
`$profileContent = Get-Content -Path `$PROFILE -ErrorAction SilentlyContinue

if (`$profileContent) {
    `$newContent = @()
    `$inCommandBlock = `$false
    `$currentCommand = ""
    
    # Process each line in the profile
    foreach (`$line in `$profileContent) {
        # Check if line starts a function definition for one of our commands
        `$functionMatch = `$line -match "^function (.*) \{$"
        if (`$functionMatch) {
            `$potentialCommand = `$Matches[1]
            if (`$commandsToRemove -contains `$potentialCommand) {
                `$inCommandBlock = `$true
                `$currentCommand = `$potentialCommand
                continue
            }
        }
        
        # Check if we're exiting a command block
        if (`$inCommandBlock -and `$line -match "^\}$") {
            `$inCommandBlock = `$false
            # Remove the command from the list
            `$commandsToRemove.Remove(`$currentCommand)
            continue
        }
        
        # If not in a command block, keep the line
        if (-not `$inCommandBlock) {
            `$newContent += `$line
        }
    }
    # Write the new content back to the profile
    Set-Content -Path `$PROFILE -Value `$newContent

    # If there are any commands left in the list, they were not found in the profile
    if (`$commandsToRemove.Count -gt 0) {
        Write-Host "Commands not removed:" -ForegroundColor Red
        foreach (`$command in `$commandsToRemove) {
            Write-Host " - `$command" -ForegroundColor Red
        }
    }
    else {
        Write-Host "All specified commands have been removed." -ForegroundColor Green
    }
} else {
    Write-Host "PowerShell profile not found. Nothing to uninstall." -ForegroundColor Yellow
}
"@

Set-Content -Path "$scriptPath\uninstall_windows.ps1" -Value $uninstallContent
Write-Host "Created uninstall script at $scriptPath\uninstall_windows.ps1" -ForegroundColor Green