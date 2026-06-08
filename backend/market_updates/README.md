# Market Updates SMS

This folder contains a standalone market update SMS module for Tech Restore internal use.

It is intentionally isolated from the main backend routes and Twilio voicemail flow.

## Required environment variables

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER` or existing repo-compatible `TWILIO_PHONE_NUMBER`

Recipient configuration (one is required):

- `MARKET_UPDATE_TO_NUMBERS` (preferred, comma-separated)
- `MARKET_UPDATE_TO_NUMBER` (single recipient fallback)

## Optional environment variables

- `MARKET_UPDATE_SYMBOLS` as a comma-separated symbol list.
  - Default: `^GSPC,BTC-USD`
- `MARKET_UPDATE_PROVIDER`
  - Default: `yfinance`

## Supported yfinance symbols

- S&P 500: `^GSPC`
- Nasdaq Composite: `^IXIC`
- Dow Jones: `^DJI`
- Bitcoin USD: `BTC-USD`
- Ethereum USD: `ETH-USD`

## CLI usage

From `tech-restore-desk/backend`:

Dry run (fetch + format + print only):

```powershell
python -m market_updates.send_market_update --dry-run
```

Real send:

```powershell
python -m market_updates.send_market_update
```

Override destination number for one run:

```powershell
python -m market_updates.send_market_update --to +15555550123
```

Override with multiple recipients for one run:

```powershell
python -m market_updates.send_market_update --to +18483291230,+19296529336
```

Schedule a one-time send at local time (HH:MM, 24-hour):

```powershell
python -m market_updates.send_market_update --send-at 14:40
```

If the requested time already passed today, the command exits with an error unless you explicitly add `--tomorrow`.
For a 2:40 PM Eastern send, run this on a machine set to Eastern time / America/New_York.

## Inbound SMS keyword menu

Inbound Twilio SMS webhook route:

`POST /api/market-updates/sms`

Point Twilio Messaging webhook for your Twilio number to that route.

Supported top-level keywords:

- `HELP`
- `MENU`
- `CHECK`
- `REMIND`
- `LIST`
- `STOP`
- `CANCEL`

The flow is stateful by sender phone number and stored in a dedicated SQLite file.

## Notification runner

Run notification checks manually:

```powershell
python -m market_updates.notification_runner --dry-run
python -m market_updates.notification_runner
```

## Local webhook simulation (PowerShell)

Run these against a local API instance:

```powershell
Invoke-WebRequest `
  -Uri "http://localhost:8787/api/market-updates/sms" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -UseBasicParsing `
  -Body "From=%2B18483291230&Body=HELP&MessageSid=SMTEST123"
```

```powershell
Invoke-WebRequest `
  -Uri "http://localhost:8787/api/market-updates/sms" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -UseBasicParsing `
  -Body "From=%2B18483291230&Body=CHECK&MessageSid=SMTEST124"
```

```powershell
Invoke-WebRequest `
  -Uri "http://localhost:8787/api/market-updates/sms" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -UseBasicParsing `
  -Body "From=%2B18483291230&Body=BTC&MessageSid=SMTEST125"
```

Expected outcomes:

- HTTP `200`
- XML/TwiML response body
- `HELP` includes the market assistant menu
- `CHECK` includes the market choices menu

## Example .env values (fake only)

```dotenv
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=twilio_auth_token_example_only
TWILIO_FROM_NUMBER=+15555550001
MARKET_UPDATE_TO_NUMBERS=+18483291230,+19296529336
MARKET_UPDATE_SYMBOLS=^GSPC,^IXIC,BTC-USD
MARKET_UPDATE_PROVIDER=yfinance
```

## Command examples for this workspace

Dry run from backend folder:

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --dry-run
```

Real send now:

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update
```

Send once at 2:40 PM local time (run this on a machine set to Eastern time for 2:40 PM Eastern behavior):

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --send-at 14:40
```

Dry run for the two current recipient numbers:

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --dry-run --to +18483291230,+19296529336
```
