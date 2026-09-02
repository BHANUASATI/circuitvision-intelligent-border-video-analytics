# SSL Certificates

Place your TLS certificate files here:

- `server.crt` — Full-chain certificate (your cert + intermediates)
- `server.key` — Private key (keep permissions 600, never commit to git)

## Development (self-signed)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/server.key \
  -out nginx/ssl/server.crt \
  -subj "/C=IN/ST=JK/L=Jammu/O=BSF/CN=ibvap.local"
```

## Production (Let's Encrypt via certbot)

```bash
certbot certonly --standalone -d yourdomain.com
# Then symlink or copy:
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/server.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   nginx/ssl/server.key
```
