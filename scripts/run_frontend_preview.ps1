param(
    [int]$Port = 5500
)

Write-Host "Starting S.O.L.A.R frontend preview at http://localhost:$Port"
Write-Host "This is static preview mode (API calls may fail if backend is not running)."
python -m http.server $Port --directory frontend

