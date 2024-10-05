#!/usr/bin/env pwsh
# (c) MIT License, Tremeschin
#
# This PowerShell script runs depthflow for all images on a "inputs" folder
# in the current directory, and batch renders videos to "outputs"
#
# Note: Save it as "run.ps1", right click and "Run with PowerShell" to execute
#
# Note: Grab a release and rename it to "depthflow.exe" on the same folder
#
Get-ChildItem -Path "inputs" | ForEach-Object {
    $filename = $_.BaseName

    # Change or add variations and parameters here!
    .\depthflow.exe input -i $_.FullName `
        orbital `
        main -o "./outputs/$filename-orbital.mp4"

    .\depthflow.exe input -i $_.FullName `
        horizontal --intensity 0.6 `
        main -o "./outputs/$filename-horizontal.mp4" --loop 3
}

Write-Host "Press any key to continue..."