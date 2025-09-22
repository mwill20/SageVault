param([string]$OutDir = "artifacts"); mkdir $OutDir -Force | Out-Null; python -m pytest tests -q --audit-report-dir $OutDir
