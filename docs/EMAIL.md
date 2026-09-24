# Email Reporting

LBM-VDRC can send SMTP success and failure reports after jobs.

## Configure credentials

```bash
sudo lbm-vdrc credential add smtp --type generic
```

Enter the SMTP username and password/secret.

## Configure SMTP

```bash
sudo lbm-vdrc email configure
```

You will be asked for:

- SMTP server;
- port;
- security mode (`starttls`, `ssl`, or `none`);
- From address;
- recipient address;
- SMTP credential profile name.

Typical ports are provider-dependent. Use the settings published by your mail provider.

## Messages

On success, LBM-VDRC sends a message with:

```text
Job
Type
Status: SUCCESS
Duration
Result
```

On failure:

```text
Job
Type
Status: FAILED
Duration
Error
```

Do not place SMTP passwords directly in job profiles. Store them in the Credential Vault.

Designed & Developed by **antonios.mortos@outlook.com**
