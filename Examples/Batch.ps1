#!/usr/bin/env pwsh
# (c) MIT License, Tremeschin
#
# This PowerShell script runs depthflow for all images on a "input" folder
# in the current directory, and batch renders videos to "output"

if (-not (Test-Path "output")) {
    New-Item -ItemType Directory -Path "output"
}

Get-ChildItem -Path "inputs" | ForEach-Object {
    $filename = $_.BaseName

    # Change or add variations and parameters here!
    depthflow.exe input -i $_.FullName `
        main -o "./output/$filename.mp4"

    # depthflow.exe input -i $_.FullName `
    #     dolly --intensity 0.5 `
    #     main -o "./outputs/$filename-orbital.mp4"
}

Write-Host "Press any key to continue..."
