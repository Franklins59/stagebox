# Stagebox Personal - Flash SD Card

Instructions for writing the Stagebox Personal image to an SD card.

## What You Need

- **SD Card**: Minimum 8 GB, recommended 16 GB or more
- **SD Card Reader**: USB adapter or built-in card slot
- **Raspberry Pi Imager**: Free software from Raspberry Pi
- **Raspberry Pi 4 or 5**

## Step 1: Download the Image

Download the latest Stagebox Personal image:

🔗 **Download:** [https://github.com/franklins59/stagebox/releases/latest](https://github.com/franklins59/stagebox/releases/latest)

Download the file `stagebox-personal-vX.Y.Z.img.gz` (approx. 1-2 GB).

## Step 2: Install Raspberry Pi Imager

Download and install the **Raspberry Pi Imager**:

🔗 **Download:** [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

Available for:
- Windows
- macOS
- Ubuntu/Linux

## Step 3: Flash the Image

1. **Insert SD Card**
   - Insert the SD card into your computer

2. **Launch Raspberry Pi Imager**

3. **Choose Device**
   - Click "CHOOSE DEVICE"
   - Select "Raspberry Pi 4" or "Raspberry Pi 5"

4. **Choose Operating System**
   - Click "CHOOSE OS"
   - Scroll all the way down
   - Select "Use custom"
   - Navigate to the downloaded file `stagebox-personal-....img.gz`
   - **Note:** You do NOT need to extract the .gz file!

5. **Choose Storage**
   - Click "CHOOSE STORAGE"
   - Select your SD card
   - ⚠️ **Warning:** Make sure you select the correct card - all data will be erased!

6. **Skip Customization**
   - When asked "Would you like to apply OS customisation settings?" → Select **NO**
   - Stagebox settings are already included in the image

7. **Start Writing**
   - Click "WRITE"
   - Confirm with "YES"
   - Wait until the process completes

### Note About Progress (>100%)

The Raspberry Pi Imager sometimes shows progress over 100% (e.g., 250% or 457%). **This is normal and not an error!**

**Why does this happen?**
The image is compressed (.gz format). The Imager calculates progress based on the compressed file size (~1.5 GB), but writes the uncompressed data (~4-7 GB). This causes the displayed value to exceed 100%.

**Just wait** – the process will complete successfully.

## Step 4: First Boot

After flashing:

1. **Remove SD card** and insert it into the Raspberry Pi
2. **Connect network cable** (Ethernet recommended)
3. **Connect power**

### What Happens During First Boot?

The first boot takes **2-3 minutes** longer than usual. The following is automatically configured:

| Phase | What Happens | Duration |
|-------|--------------|----------|
| 1. Expand partition | SD card is fully utilized | ~1-2 min |
| 2. Security keys | SSH keys are generated | ~10 sec |
| 3. Set hostname | Device receives unique name | ~5 sec |
| 4. Start Stagebox | Web interface is started | ~30 sec |

**Indicators:**
- The green LED on the Pi blinks intensively during setup
- After completion, it only blinks occasionally

### When is Stagebox Ready?

Stagebox is ready when you can reach the web interface:

1. **Find IP Address**
   - Check your router for the new device
   - The hostname starts with `stagebox-` (e.g., `stagebox-a1b2c3`)

2. **Open Web Interface**
   - Open a browser
   - Enter: `http://[IP-ADDRESS]:5000`
   - Example: `http://192.168.1.100:5000`

## Frequently Asked Questions

### The web interface is not reachable?

- Wait 3-4 minutes after powering on
- Check if the network cable is properly connected
- Check if the green LED is still blinking intensively (then keep waiting)

### Which SD card is recommended?

| Type | Speed | Recommendation |
|------|-------|----------------|
| SanDisk Ultra | Good | ✓ Works |
| SanDisk Extreme | Very good | ✓✓ Recommended |
| SanDisk Extreme Pro | Excellent | ✓✓✓ Best choice |
| No-name cards | Variable | ⚠️ Not recommended |

Minimum **Class 10** or **A1** rating.

### Can I flash the image to multiple SD cards?

Yes! Each Stagebox automatically receives during first boot:
- A unique hostname
- Its own security keys
- Its own device ID

You can use the same image as many times as you want.

### Do I need to extract the .gz file?

**No!** The Raspberry Pi Imager can read compressed .gz files directly. Extracting is not necessary and would only use additional storage space.

### How do I get updates?

Stagebox Personal receives updates directly from GitHub. In the web interface under **System → Updates** you can check for new versions and install them.

## Support & Community

Stagebox Personal is open source. For questions or issues:

- 🐛 **Issues:** [github.com/franklins59/stagebox/issues](https://github.com/franklins59/stagebox/issues)
- 📖 **Documentation:** [github.com/franklins59/stagebox](https://github.com/franklins59/stagebox)
- 🌐 **Website:** [franklins.forstec.ch](https://franklins.forstec.ch)

---

**Stagebox Pro** with advanced features (Multi-Building, USB Backup, Snapshots) is available as a hardware product: [franklins.forstec.ch](https://franklins.forstec.ch)