param([string]$OutDir = "artifacts");
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path;
Push-Location $scriptDir;
try {
	mkdir $OutDir -Force | Out-Null;
	python -m pytest tests -q --audit-report-dir $OutDir
}
finally {
	Pop-Location
}
