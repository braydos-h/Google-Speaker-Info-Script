function googlespeakerinfo {
    param(
        [string]$Uri      = 'http://192.168.8.110:8008/setup/eureka_info?options=detail',
        [int]   $Interval = 5   # seconds
    )

    # ── ANSI helper ────────────────────────────────────────────────────────────────
    $esc = [char]27
    function Color { param([string]$code, [string]$text) "$esc[$code${text}$esc[0m" }

    # ── Pretty-printer ─────────────────────────────────────────────────────────────
    function Print {
        param([string]$Label, [object]$Value, [string]$Colour = '37m')
        $pad = ($Label + ':').PadRight(18)
        Write-Host "$(Color '1;36m' $pad) $(Color $Colour $Value)"
    }

    while ($true) {
        try     { $j = Invoke-RestMethod $Uri -ErrorAction Stop }
        catch   { Write-Host (Color '31m' "❌  $($_.Exception.Message)"); Start-Sleep $Interval; continue }

        Clear-Host

        # Derived values
        $bootUtc      = (Get-Date).ToUniversalTime().AddSeconds(-$j.uptime)
        $upSpan       = [timespan]::FromSeconds($j.uptime)
        $updateColour = if ($j.has_update) { '93m' } else { '90m' }

        # Wi-Fi RSSI to colour
        $wifiColour = switch ($j.signal_level) {
            { $_ -ge -55 } { '92m' }   # excellent
            { $_ -ge -65 } { '93m' }   # fair
            default        { '91m' }   # poor
        }

        # ── Header ────────────────────────────────────────────────────────────────
        $title = ' Google-Speaker Info '
        Write-Host (Color '1;45m' $title).PadRight([console]::WindowWidth, ' ')
        Write-Host

        # ── Body ─────────────────────────────────────────────────────────────────
        Print 'Timestamp'        (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        Print 'Name'             $j.name                    '92m'
        Print 'Build Revision'   $j.cast_build_revision
        Print 'Track'            $j.release_track
        Print 'Update Pending'   $j.has_update              $updateColour
        Print 'Uptime'           $upSpan.ToString('dd\.hh\:mm\:ss')
        Print 'Boot (UTC)'       $bootUtc.ToString('yyyy-MM-dd HH:mm:ss')
        Write-Host

        Print 'SSID'             $j.ssid
        Print 'BSSID'            $j.bssid
        Print 'Wi-Fi RSSI'       "$($j.signal_level) dBm"   $wifiColour
        Print 'Noise Floor'      "$($j.noise_level) dBm"
        Print 'IP Address'       $j.ip_address
        Print 'MAC Address'      $j.mac_address
        Print 'Ethernet'         $j.ethernet_connected
        Write-Host

        Print 'Locale'           $j.locale
        Print 'Country'          $j.location.country_code
        Print 'Fuchsia Version'  $j.version
        Print 'Time-Zone'        $j.timezone
        Print 'Opt-In Crash'     $j.opt_in.crash
        Print 'Opt-In Stats'     $j.opt_in.stats
        Write-Host

        Write-Host (Color '90m' 'Green = good · Yellow = meh · Red = bad/needs attention')
        Start-Sleep $Interval
    }
}

# ── Kick it off ──────────────────────────────────────────────────────────────────
googlespeakerinfo -Interval 5
