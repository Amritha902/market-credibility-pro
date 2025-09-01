param(
    [string]$ProjectPath = "C:\Users\amrit\Downloads\market-credibility-pro-ingest",
    [string]$RepoUrl = "https://github.com/Amritha902/market-credibility-pro.git",
    [string]$CommitMsg = "Initial clean commit: code only"
)

Write-Host ">>> Using ProjectPath: $ProjectPath"
if (!(Test-Path $ProjectPath)) {
    Write-Error "Project path not found: $ProjectPath"
    exit 1
}
Set-Location $ProjectPath

# Remove existing .git to avoid pushing huge history
if (Test-Path ".git") {
    Write-Host ">>> Removing existing .git (clean reset)"
    Remove-Item -Recurse -Force ".git"
}

# Write .gitignore
$gitignoreContent = @"
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.pytest_cache/

# Environments / IDE
.venv/
venv/
env/
.vscode/
.idea/
*.code-workspace

# Data & logs (runtime outputs)
*.log
*.jsonl
evidence_log.jsonl
samples/ingested.csv

# Archives / binaries
*.zip
*.7z
*.tar
*.tar.gz
*.pkl
*.sav
*.sqlite

# Streamlit / cache
.streamlit/
**/.cache/
"@
Set-Content -Path ".gitignore" -Value $gitignoreContent -Encoding UTF8

# Init, add, commit
git init
git add .
git commit -m $CommitMsg

# Connect remote and push
git remote add origin $RepoUrl
git branch -M main
git push -u origin main
