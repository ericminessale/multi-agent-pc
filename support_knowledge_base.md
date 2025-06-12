# PC Builder Pro - Technical Support Knowledge Base

## Initial Diagnostics

### First Contact Protocol
1. Get order number or serial number (starts with PCB-YYYY-XXXXX)
2. Verify warranty status (3 years from ship date)
3. Ask about recent changes (new hardware, software updates, physical moves)
4. Document symptoms precisely
5. Check support ticket history for recurring issues

### System Information Gathering
- **Windows**: Have customer run "msinfo32" and read System Summary
- **BIOS Version**: Restart and note version on POST screen
- **Temperatures**: Use HWMonitor or Core Temp
- **Event Viewer**: Check for critical errors in past 7 days

## Common Issues & Solutions

### Power & Boot Issues

#### System Won't Power On At All
**Symptoms**: No lights, no fans, completely dead

**Diagnostic Steps**:
1. **Check Power Cable**: Ensure firmly connected at both ends
2. **Test Wall Outlet**: Try different outlet or test with phone charger
3. **Check PSU Switch**: Verify switch on back of PSU is ON (|)
4. **Check Power Button Connection**: 
   - Open case
   - Locate PWR SW cable on motherboard (usually bottom right)
   - Ensure firmly connected to correct pins

**Resolution**:
- If still dead: PSU likely failed - initiate RMA
- If lights but no boot: Continue to POST issues

#### Powers On But No Display (No POST)
**Symptoms**: Fans spin, lights on, but no display

**Diagnostic Steps**:
1. **Monitor Check**:
   - Try different cable (HDMI/DisplayPort)
   - Ensure monitor powered on and correct input selected
   - Connect to motherboard video (if available) instead of GPU
2. **RAM Reseat**:
   - Power off completely
   - Remove all RAM sticks
   - Insert ONE stick in slot A2 (2nd from CPU)
   - Try boot
3. **Clear CMOS**:
   - Unplug power
   - Remove CMOS battery for 60 seconds
   - OR use Clear CMOS jumper (check motherboard manual)
4. **GPU Reseat**:
   - Remove GPU completely
   - Check for bent pins in PCIe slot
   - Firmly reinstall, ensure power cables connected

**Resolution Tree**:
- Works with integrated graphics → GPU issue
- Works with 1 RAM stick → Bad RAM or slot
- Still no display → Motherboard or CPU issue

#### System Randomly Shuts Off
**Symptoms**: PC turns off suddenly during use

**Temperature Check**:
1. Download HWMonitor
2. Run stress test (Prime95 for CPU, FurMark for GPU)
3. Monitor temps:
   - CPU: Should stay under 85°C
   - GPU: Should stay under 83°C

**If Overheating**:
- Check all fans are spinning
- Verify AIO pump working (feel for vibration)
- Check thermal paste (if over 2 years old)
- Clean dust filters

**If Temperatures Normal**:
- Check Event Viewer for WHEA errors (PSU issue)
- Run MemTest86 overnight (RAM issue)
- Check PSU calculator - system may exceed wattage

### Performance Issues

#### Low FPS in Games
**Diagnostic Questions**:
1. Which specific games?
2. What resolution and settings?
3. Recent driver updates?
4. Background applications running?

**Step-by-Step Resolution**:
1. **Update Graphics Drivers**:
   - Use DDU (Display Driver Uninstaller) in Safe Mode
   - Download latest from NVIDIA/AMD directly
   - Clean install
2. **Check Power Settings**:
   - Windows Power Plan: High Performance
   - NVIDIA Control Panel: Prefer Maximum Performance
   - Disable Xbox Game Bar and Game Mode
3. **Monitor Thermals During Gaming**:
   - Use MSI Afterburner overlay
   - Check for thermal throttling
4. **Verify RAM Running at Rated Speed**:
   - Check Task Manager → Performance → Memory
   - If showing 2133MHz instead of rated speed:
     - Enter BIOS
     - Enable XMP/DOCP profile

**Expected Performance** (match to customer's build):
- Entry Build: See sales KB for FPS targets
- Performance Build: See sales KB for FPS targets
- Ultimate Build: Should max any game

#### System Freezes/Hangs
**Types of Freezes**:
1. **Complete Freeze** (no cursor movement)
   - Usually hardware: RAM, SSD, or PSU
2. **Application Freeze** (cursor moves)
   - Usually software: Drivers or Windows

**Hardware Freeze Diagnosis**:
1. **RAM Test**:
   ```
   - Download MemTest86
   - Create bootable USB
   - Run overnight (8+ hours)
   - Any errors = RMA RAM
   ```
2. **Storage Test**:
   ```
   - CrystalDiskInfo for health check
   - If "Caution" or "Bad" = RMA drive
   - Run chkdsk /f /r from admin command prompt
   ```
3. **PSU Test**:
   - Freezes under load = PSU failing
   - Use OCCT Power Supply test

**Software Freeze Resolution**:
1. Update all drivers (use Driver Booster)
2. Windows Update fully
3. Disable startup programs
4. Clean boot troubleshooting

### Blue Screen of Death (BSOD)

#### Common BSOD Codes

**MEMORY_MANAGEMENT**
- Cause: Faulty RAM or incompatible speeds
- Fix: 
  1. Run Windows Memory Diagnostic
  2. Test with one stick at a time
  3. Ensure matched pairs
  4. Disable XMP and test

**DRIVER_IRQL_NOT_LESS_OR_EQUAL**
- Cause: Driver conflict
- Fix:
  1. Boot Safe Mode
  2. Uninstall recent driver updates
  3. Use Driver Verifier to identify problem driver

**SYSTEM_SERVICE_EXCEPTION**
- Cause: Corrupted system files
- Fix:
  1. Run: sfc /scannow
  2. Run: DISM /Online /Cleanup-Image /RestoreHealth
  3. If persists, Windows repair install

**WHEA_UNCORRECTABLE_ERROR**
- Cause: Hardware failure (CPU, PSU, Motherboard)
- Fix:
  1. Check CPU temps
  2. Disable CPU overclock
  3. Test with different PSU
  4. Usually requires RMA

### Hardware-Specific Issues

#### RGB Lighting Not Working
**Software Check**:
1. Install correct software:
   - ASUS: Aura Sync
   - MSI: Mystic Light
   - Gigabyte: RGB Fusion
   - Corsair: iCUE
2. Check for conflicts between RGB software

**Hardware Check**:
1. Verify RGB headers connected
2. Check header type (12V RGB vs 5V ARGB - NOT interchangeable!)
3. Maximum LED strips per header (usually 2-3)

#### USB Devices Disconnecting
**Common Causes**:
1. **Power Saving**: 
   - Device Manager → USB Root Hub → Properties
   - Power Management → Uncheck "Allow computer to turn off"
2. **USB Selective Suspend**:
   - Power Options → Advanced → USB Settings → Disabled
3. **Faulty Port**:
   - Test different ports
   - Front panel USB often problematic

#### No Sound/Audio Issues
**Quick Fixes**:
1. Right-click speaker icon → Troubleshoot
2. Ensure correct playback device selected
3. Check cable connection (green port for speakers)
4. Update Realtek/audio drivers

**Advanced**:
1. Disable audio enhancements
2. Change sample rate to 44.1kHz
3. Reinstall audio drivers in Device Manager

### Software & Windows Issues

#### Windows Activation Problems
**For OEM Keys We Provide**:
1. Run: slmgr /ipk [product-key]
2. Run: slmgr /ato
3. If fails, call Microsoft activation: 1-888-571-2048
4. We can provide proof of purchase

#### Slow Boot Times
**Expected Boot Times**:
- NVMe SSD: 10-20 seconds
- SATA SSD: 20-30 seconds

**If Slower**:
1. Disable unnecessary startup programs
2. Check if Windows Fast Startup enabled
3. Update SSD firmware
4. Check BIOS for slow POST (disable memory training)

#### Driver Conflicts
**Clean Driver Install Process**:
1. Download all drivers first:
   - Chipset (AMD/Intel)
   - GPU (NVIDIA/AMD)
   - Audio (Realtek)
   - LAN (Intel/Realtek)
   - Storage (if NVMe)
2. DDU graphics in Safe Mode
3. Install in order: Chipset → GPU → Others
4. Reboot between each

### Network & Connectivity

#### Ethernet Not Working
1. Check cable (try different one)
2. Update network adapter driver
3. Reset network stack:
   ```
   netsh winsock reset
   netsh int ip reset
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```

#### WiFi Issues (If Equipped)
1. Check antenna connected to WiFi card
2. Update WiFi drivers
3. Change router channel (2.4GHz: 1,6,11)
4. Disable WiFi power saving

### Storage Issues

#### SSD Not Detected
**In BIOS**:
1. Check SATA/NVMe enabled
2. Try different SATA port/cable
3. Update BIOS

**In Windows (New Drive)**:
1. Disk Management → Initialize Disk
2. Create New Simple Volume
3. Assign drive letter

#### Slow SSD Performance
**Expected Speeds**:
- Gen4 NVMe: 5000+ MB/s read
- Gen3 NVMe: 3500 MB/s read
- SATA SSD: 550 MB/s read

**If Slower**:
1. Check correct slot (GPU may share bandwidth)
2. Update firmware
3. Ensure proper cooling (thermal throttling)
4. Check if drive full (keep 20% free)

## Advanced Troubleshooting

### Stress Testing Tools
- **CPU**: Prime95 (Small FFTs for heat, Blend for stability)
- **GPU**: FurMark, Unigine Heaven
- **RAM**: MemTest86, HCI MemTest
- **Storage**: CrystalDiskMark, ATTO
- **Full System**: OCCT, AIDA64

### When to RMA Components

#### Definite RMA Scenarios:
- Physical damage (bent pins, burn marks)
- MemTest86 errors
- SMART errors on SSD
- Consistent WHEA errors
- GPU artifacts (green/pink pixels)
- Coil whine louder than normal

#### RMA Process:
1. Document issue with photos/videos
2. Note troubleshooting steps tried
3. Contact support with order number
4. We'll provide RMA number and shipping label
5. Pack in anti-static bag
6. Include copy of invoice

### BIOS Settings Guide

#### First Boot Setup:
1. Enable XMP/DOCP for RAM
2. Set fan curves (CPU: 30% at 40°C, 100% at 80°C)
3. Disable CSM for Windows 11
4. Enable Resizable BAR (if supported)

#### Overclock Failed:
1. Clear CMOS
2. Load optimized defaults
3. Only change one setting at a time
4. Stress test each change

## Escalation Guidelines

### When to Escalate to Senior Tech:
- Hardware failure confirmed needing RMA
- Customer requesting manager
- Issue persists after 30 minutes troubleshooting
- Potential safety issue (burning smell, sparks)
- Custom loop liquid cooling problems

### Documentation for Escalation:
- Order/Serial number
- Issue description
- Steps tried
- Test results (temps, benchmarks)
- Customer mood/satisfaction level

## Safety Warnings

### Always Remind Customers:
- Unplug power before working inside case
- Touch case metal to discharge static
- Never force components
- Don't mix modular PSU cables between units
- Never plug 12V RGB into 5V header (will destroy LEDs)

### Liquid Cooling Warnings:
- Check for leaks monthly
- AIO lifespan: 5-7 years
- Pump should be lower than radiator top
- Gurgling sounds = air in pump (reposition)