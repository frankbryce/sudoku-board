# DoDad Puzzles™ Mailing List Setup (Google Sheets + Apps Script)

This folder contains the tiny Google Apps Script ([`Code.gs`](Code.gs)) that connects the signup forms on **dodadpuzzles.com** to a private **Google Sheet** in your Google Drive, with a dedicated **`Gmail BCC`** tab so you can copy/paste everyone into Gmail's **Bcc** field in one click.

## 2-Minute Setup

1. **Create a Google Sheet** in your Google Drive (e.g. `DoDad Puzzles Mailing List`).
2. In the Sheet menu, open **Extensions → Apps Script**.
3. Delete any default `myFunction()` code in `Code.gs`, paste in the full contents of [`mailing-list/Code.gs`](Code.gs), and click **Save** (floppy disk icon).
4. In the Apps Script toolbar, select **`setupSheet`** from the function dropdown and click **Run** (grant permission to your own Google Sheet when prompted).
   - This creates two tabs:
     - **`Subscribers`** — `Timestamp`, `Email`, `Interests`, `Source`, `Status` (automatically deduplicates repeat signups).
     - **`Gmail BCC`** — Live comma-separated lists for **All Active Subscribers**, **Shipped 4×4 Kits**, and **New Free Puzzles & STLs**.
5. Click **Deploy → New deployment**:
   - Type: **Web app**
   - Description: `DoDad Puzzles Mailing List`
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy**, then copy the **Web app URL** (`https://script.google.com/macros/s/.../exec`).
6. Paste that URL into [`docs/site-config.js`](../docs/site-config.js):
   ```js
   mailingList: Object.freeze({
     endpoint: "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
   }),
   ```
7. Commit and push to GitHub — both signup forms on `dodadpuzzles.com` (the main Mailing List section and the Shipped Sets dialog) will immediately save directly to your Sheet.

## Sending an Email in Gmail

1. Open your Google Sheet and click the **`Gmail BCC`** tab.
2. Click cell **`C2`** (All Active Subscribers), **`C3`** (Shipped 4×4 Kits), or **`C4`** (New Free Puzzles & STLs) and press **Ctrl+C / Cmd+C**.
3. In Gmail, click **Compose**, put your own address in **To**, click **Bcc**, and press **Ctrl+V / Cmd+V**.
4. Paste the ready-made unsubscribe footer (also saved in cell **`C6`** of the **`Gmail BCC`** tab) at the bottom of your email:
   > You received this because you signed up for DoDad Puzzles updates. Unsubscribe anytime: https://dodadpuzzles.com/unsubscribe/ | DoDad Puzzles LLC • Sewickley, PA 15143

## How Unsubscribing Works

- **Self-serve (from your emails or the website):** Anyone can visit **https://dodadpuzzles.com/unsubscribe/** (linked from your email footer, the signup form, the site footer, and the Privacy Policy), enter their email, and click **Unsubscribe Me**.
- **Automatic Sheet update:** `Code.gs` marks their `Status` column (column E) as `unsubscribed`, and they immediately drop out of all **`Gmail BCC`** cells.
- **Manual fallback:** You can also change someone's `Status` from `active` to `unsubscribed` directly in the **`Subscribers`** tab.

## Updating `Code.gs` Without Changing Your Web App URL

Whenever `mailing-list/Code.gs` is updated:
1. Paste the updated `Code.gs` into **Extensions → Apps Script** and click **Save**.
2. Click **Deploy → Manage deployments** → click the **Edit (pencil)** icon on your active deployment.
3. Under **Version**, choose **New version** and click **Deploy**. (This keeps the exact same `exec` URL in `docs/site-config.js`!)

