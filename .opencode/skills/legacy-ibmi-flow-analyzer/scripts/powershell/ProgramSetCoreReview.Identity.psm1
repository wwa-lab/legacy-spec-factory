<#
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

Output-bundle identity guard for the native PowerShell reader-first merger.
#>
#requires -version 5.1

Set-StrictMode -Version 2.0

Import-Module (Join-Path $PSScriptRoot 'FlowYaml.psm1') -Force

function Get-IdentityMapValue {
    param($Map, [Parameter(Mandatory = $true)][string]$Key, $Default = $null)
    if ($null -eq $Map) { return $Default }
    if ($Map -is [System.Collections.IDictionary]) {
        if ($Map.Contains($Key)) { return $Map[$Key] }
        return $Default
    }
    $property = $Map.PSObject.Properties[$Key]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Get-FlowBundleIdentity {
    param($Manifest)
    $documentId = [string](Get-IdentityMapValue $Manifest 'document_id' (Get-IdentityMapValue $Manifest 'review_id' ''))
    $flowSlug = [string](Get-IdentityMapValue $Manifest 'flow_slug' '')
    $programSetSlug = [string](Get-IdentityMapValue $Manifest 'program_set_slug' '')
    $canonical = [string](Get-IdentityMapValue $Manifest 'canonical_filename' '')
    $programs = @(
        @(Get-IdentityMapValue $Manifest 'programs' @()) |
            ForEach-Object { [string](Get-IdentityMapValue $_ 'normalized_name' '') } |
            Where-Object { $_ } |
            Sort-Object -Unique
    )
    return @($documentId, $flowSlug, $programSetSlug, $canonical, ($programs -join ',')) -join '|'
}

function Assert-FlowOutputIdentityCompatible {
    param([Parameter(Mandatory = $true)][string]$ManifestPath, $Manifest)
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { return }
    $existing = Read-FlowYamlFile $ManifestPath
    if ($existing -isnot [System.Collections.IDictionary]) {
        throw "existing bundle manifest is not a YAML mapping: $ManifestPath"
    }
    $existingIdentity = Get-FlowBundleIdentity $existing
    $requestedIdentity = Get-FlowBundleIdentity $Manifest
    if (-not $existingIdentity.Equals($requestedIdentity, [StringComparison]::Ordinal)) {
        throw 'existing bundle manifest identity does not match the requested flow/program set'
    }
}

function Assert-FlowFormalReviewAbsent {
    param([Parameter(Mandatory = $true)][string]$ReviewPath)
    if (Test-Path -LiteralPath $ReviewPath -PathType Leaf) {
        throw "existing formal review must be explicitly archived before rebuilding the preparation bundle: $ReviewPath"
    }
}

function Remove-FlowStaleReadyArtifacts {
    param([Parameter(Mandatory = $true)][string]$Folder, [string[]]$Filenames)
    foreach ($filename in $Filenames) {
        $path = Join-Path $Folder $filename
        if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force }
    }
}

Export-ModuleMember -Function Assert-FlowOutputIdentityCompatible, Assert-FlowFormalReviewAbsent, Remove-FlowStaleReadyArtifacts
