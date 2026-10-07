# jnkie_retrieve

##basics

If you open the link, **another link** appears. If you open that, **another link** appears.

You just need to repeat this until no more new links appear. **The End.**

You are not cracking a password. You are simply opening the envelope and **copying the next address** written inside.

### What are `v=2` and `errors=text`?

- `v=2`: Delivery Protocol Version 2

- `errors=text`: A request for the reason for failure as text (→ `LDR-DENIED:...`)

## Commands

```bash

# Basic (Public Script)

python jnkie_retrieve.py "https://cdn.jnkie.com/...." --key KEYLESS

# Start over

python jnkie_retrieve.py "https://api.jnkie.com/api/v1/luascripts/public/<hash>/download"

# When you want to see every HTTP step

python jnkie_retrieve.py "<url>" --key KEYLESS --debug

```

Output when successful:

```

[*] GET loader: ...

[*] 200 3421 bytes

[*] content-address: OK

[*] delivery: https://api.jnkie.com/api/v1/luascripts/delivery/....

[*] POST key ('KEYLESS') ...

[*] delivery response: 200

[*] signed URL: https://cdn.jnkie.com/....lua

[*] 200 284013 bytes

[+] wrote e57443....lua (284013 bytes)

**What works**

- Jinke scripts set to 'Public'
