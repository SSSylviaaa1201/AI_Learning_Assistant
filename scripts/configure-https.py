"""Run on the owner's ECS; receive gateway credentials through stdin."""
from pathlib import Path
import crypt
import json
import secrets
import subprocess
import sys

credentials=json.load(sys.stdin)
username=credentials['username']
assert username.isalnum()
password_hash=crypt.crypt(credentials['password'],crypt.mksalt(crypt.METHOD_SHA512))
passwd_path=Path('/etc/nginx/.htpasswd-ai-learning-assistant')
passwd_path.write_text(username+':'+password_hash+'\n')
subprocess.run(['chown','root:www-data',str(passwd_path)],check=True)
passwd_path.chmod(0o640)
gate=secrets.token_urlsafe(48)
maps=Path('/etc/nginx/conf.d/aila-access.conf')
maps.write_text('''# Separate proxy gate from the application's bearer-token login.
map_hash_bucket_size 128;
map $cookie_aila_proxy_session $aila_auth_realm {
    default "AI Learning Assistant";
    "GATE_TOKEN" off;
}
map "$status:$remote_user" $aila_session_cookie {
    default "";
    ~^200:.+ "aila_proxy_session=GATE_TOKEN; Path=/; Secure; HttpOnly; SameSite=Strict";
}
'''.replace('GATE_TOKEN',gate))
maps.chmod(0o600)
site=Path('/etc/nginx/sites-available/ai-learning-assistant')
site.write_text('''server {
    listen 80;
    listen [::]:80;
    server_name sunyinluo.asia;
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
        default_type text/plain;
        try_files $uri =404;
    }
    location / { return 308 https://sunyinluo.asia$request_uri; }
}
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sunyinluo.asia;
    ssl_certificate /etc/letsencrypt/live/sunyinluo.asia/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sunyinluo.asia/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:AILATLS:10m;
    client_max_body_size 200m;
    auth_basic $aila_auth_realm;
    auth_basic_user_file /etc/nginx/.htpasswd-ai-learning-assistant;
    add_header Set-Cookie $aila_session_cookie;
    add_header Strict-Transport-Security "max-age=15552000" always;
    add_header X-Content-Type-Options nosniff always;
    location / {
        proxy_pass http://127.0.0.1:14242;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 360s;
        proxy_send_timeout 360s;
        proxy_buffering off;
    }
}
''')
subprocess.run(['nginx','-t'],check=True)
subprocess.run(['systemctl','reload','nginx'],check=True)
hook=Path('/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh')
hook.parent.mkdir(parents=True,exist_ok=True)
hook.write_text('#!/bin/sh\nnginx -t && systemctl reload nginx\n')
hook.chmod(0o750)
print('HTTPS, Basic authentication, bearer-compatible gateway cookie, and renewal hook configured. No credentials printed.')
