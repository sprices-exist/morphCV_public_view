$output = "output1.txt"
$root = Get-Location

# Get folder structure
$structure = Get-ChildItem -Recurse | 
    ForEach-Object {
        $_.FullName.Replace($root.Path, '').TrimStart('\')
    }

# Get content from .py and .html files
$content = Get-ChildItem -Recurse -Include *.py, *.html, *.yml | 
    ForEach-Object {
        "----- FILE: $($_.FullName) -----`n" + (Get-Content $_.FullName -Raw)
    }

# Combine and save
@(
    "=== Folder & File Structure ==="
    $structure
    "`n=== File Contents (.py and .html) ==="
    $content
) | Set-Content -Path $output -Encoding UTF8
