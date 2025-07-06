$output = "output1.txt"
$root = Get-Location

# Get folder structure excluding node_modules
$structure = Get-ChildItem -Recurse -Directory |
    Where-Object { $_.FullName -notmatch '\\node_modules\\' } |
    ForEach-Object {
        $_.FullName.Replace($root.Path, '').TrimStart('\')
    }

# Get content from specified file types excluding node_modules
$content = Get-ChildItem -Recurse -Include *.tsx, *.json, *.md, *.ts -File |
    Where-Object { $_.FullName -notmatch '\\node_modules\\' } |
    ForEach-Object {
        "----- FILE: $($_.FullName) -----`n" + (Get-Content $_.FullName -Raw)
    }

# Combine and save
@(
    "=== Folder & File Structure ==="
    $structure
    "`n=== File Contents (.tsx, .json, .md, .ts) ==="
    $content
) | Set-Content -Path $output -Encoding UTF8
