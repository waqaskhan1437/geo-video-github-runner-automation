param(
    [string]$RunDate = (Get-Date -Format 'yyyy-MM-dd'),
    [int]$Count = 3,
    [string]$Mode = 'generated',
    [string]$Engine = 'pillow',
    [switch]$WithVoice,
    [string]$PiperModel = ''
)

$ErrorActionPreference = 'Stop'

if (!(Test-Path .venv)) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

$cmd = @('run.py', 'batch', '--date', $RunDate, '--count', $Count, '--mode', $Mode, '--engine', $Engine)
if ($WithVoice) {
    $cmd += '--with-voice'
    if ($PiperModel -ne '') {
        $cmd += @('--piper-model', $PiperModel)
    }
}

python @cmd
