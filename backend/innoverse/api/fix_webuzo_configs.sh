#!/bin/bash
# Auto-fix Webuzo's midnight config resets
# Runs daily at 1:00 AM

LOG_FILE="/home/sailo/innoverse/logs/webuzo_fix.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "========================================" >> "$LOG_FILE"
echo "[$TIMESTAMP] Starting configuration fixes..." >> "$LOG_FILE"

# ============================================
# 1. FIX /etc/hosts - Remove localhost entry
# ============================================
echo "[$TIMESTAMP] Fixing /etc/hosts..." >> "$LOG_FILE"
if grep -q "127.0.0.1 innoversebd.bdix.cloud" /etc/hosts; then
    sudo sed -i '/127.0.0.1 innoversebd.bdix.cloud/d' /etc/hosts
    echo "[$TIMESTAMP] ✓ Removed localhost entry from /etc/hosts" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ✓ /etc/hosts already correct" >> "$LOG_FILE"
fi

# ============================================
# 2. FIX HTTPS Listener in httpd_config.conf
# ============================================
echo "[$TIMESTAMP] Fixing HTTPS listener in httpd_config.conf..." >> "$LOG_FILE"

HTTPD_CONFIG="/usr/local/lsws/conf/httpd_config.conf"
BACKUP_DIR="/home/sailo/innoverse/backup_configs"
mkdir -p "$BACKUP_DIR"

# Backup original config
sudo cp "$HTTPD_CONFIG" "$BACKUP_DIR/httpd_config.conf.$(date +%Y%m%d_%H%M%S)"

# Create the correct HTTPS listener block
CORRECT_HTTPS_LISTENER='listener Default-HTTPS-103.169.161.8 {
  address                 103.169.161.8:443
  secure                  1
  map                     innoversebd.bdix.cloud-443 innoversebd.bdix.cloud
  keyFile                 /etc/letsencrypt/live/innoversebd.bdix.cloud/privkey.pem
  certFile                /etc/letsencrypt/live/innoversebd.bdix.cloud/fullchain.pem
  certChain               1
  sslProtocol             24
  enableECDHE             1
  renegProtection         1
  sslSessionCache         1
  sslSessionTickets       1
  enableSpdy              15
  enableStapling          1
  ocspRespMaxAge          86400
}'

# Use Python to replace the HTTPS listener section
sudo python3 << 'PYTHON_SCRIPT'
import re

config_file = "/usr/local/lsws/conf/httpd_config.conf"

with open(config_file, 'r') as f:
    content = f.read()

# Pattern to match the entire HTTPS listener block
pattern = r'listener Default-HTTPS-103\.169\.161\.8 \{[^}]*\}'

correct_listener = '''listener Default-HTTPS-103.169.161.8 {
  address                 103.169.161.8:443
  secure                  1
  map                     innoversebd.bdix.cloud-443 innoversebd.bdix.cloud
  keyFile                 /etc/letsencrypt/live/innoversebd.bdix.cloud/privkey.pem
  certFile                /etc/letsencrypt/live/innoversebd.bdix.cloud/fullchain.pem
  certChain               1
  sslProtocol             24
  enableECDHE             1
  renegProtection         1
  sslSessionCache         1
  sslSessionTickets       1
  enableSpdy              15
  enableStapling          1
  ocspRespMaxAge          86400
}'''

# Replace the listener block
new_content = re.sub(pattern, correct_listener, content, flags=re.DOTALL)

with open(config_file, 'w') as f:
    f.write(new_content)

print("HTTPS listener updated successfully")
PYTHON_SCRIPT

echo "[$TIMESTAMP] ✓ Updated HTTPS listener with Let's Encrypt certificate" >> "$LOG_FILE"

# ============================================
# 3. FIX HTTP VHOST (Port 80)
# ============================================
echo "[$TIMESTAMP] Fixing HTTP vhost..." >> "$LOG_FILE"

HTTP_VHOST="/usr/local/lsws/conf/webuzo_vh/innoversebd.bdix.cloud-80/vhost.conf"
sudo cp "$HTTP_VHOST" "$BACKUP_DIR/vhost-80.conf.$(date +%Y%m%d_%H%M%S)"

sudo tee "$HTTP_VHOST" > /dev/null << 'EOF'
docRoot                   /home/sailo/innoverse/innoverse
vhAliases                 *
listeners                 innoversebd.bdix.cloud-80
enableGzip                1

errorlog /home/sailo/innoverse/logs/litespeed-error.log {
  useServer               0
  logLevel                ERROR
  rollingSize             10M
  compressArchive         1
}

accesslog /home/sailo/innoverse/logs/litespeed-access.log {
  useServer               0
  logFormat               %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"
  logHeaders              5
  rollingSize             10M
  keepDays                30
  compressArchive         1
}

index  {
  useServer               0
  autoIndex               0
}

# SECURITY - Block malicious patterns
context exp:^.*\.(ssh|env|git|aws|vscode|key|pwd) {
  allowBrowse             0
  rewrite  {
    enable                1
    rules                 RewriteRule .* - [F,L]
  }
}

context exp:^.*(phpinfo|wp-admin|setup-config|schema\.rb|credentials|docker-compose|config\.json|secrets\.json|service\.pwd|sftp\.json) {
  allowBrowse             0
  rewrite  {
    enable                1
    rules                 RewriteRule .* - [F,L]
  }
}

# STATIC FILES
context /static/ {
  type                    null
  location                /home/sailo/innoverse/innoverse/static/
  allowBrowse             1
  enableExpires           1
  expiresByType           */*=A2592000
  extraHeaders            <<<END_extraHeaders
Cache-Control public, immutable  
END_extraHeaders
  addDefaultCharset       off
}

context /media/ {
  type                    null
  location                /home/sailo/innoverse/innoverse/media/
  allowBrowse             1
  enableExpires           1
  expiresByType           */*=A2592000
  extraHeaders            <<<END_extraHeaders
Cache-Control public
  END_extraHeaders
  addDefaultCharset       off
}

# WEBUZO CONTEXTS
context /webuzo {
  type                    redirect
  externalRedirect        0
  statusCode              305
  location                https://innoversebd.bdix.cloud:2003
}

context /cpanel {
  type                    redirect
  externalRedirect        0
  statusCode              305
  location                https://innoversebd.bdix.cloud:2003
}

context /whm {
  type                    redirect
  externalRedirect        0
  statusCode              305
  location                https://innoversebd.bdix.cloud:2005
}

# DJANGO APPLICATION
context / {
  type                    proxy
  handler                 gunicorn_innoverse
  addDefaultCharset       off
  extraHeaders            <<<END_extraHeaders
X-Forwarded-Proto https
X-Forwarded-For %{REMOTE_ADDR}e
X-Real-IP %{REMOTE_ADDR}e
  END_extraHeaders
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
  rules                   <<<END_rules
# Force HTTPS redirect
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

# Webmail rewrite
RewriteCond %{REQUEST_URI} ^/webmail(\/*)
RewriteRule ^/(webmail)$ http://innoversebd.bdix.cloud/$1/ [R=301]
RewriteRule ^/webmail(\/*)(.*) HTTP://webuzomail/mail/$2 [P,L,E=PROXY-HOST:innoversebd.bdix.cloud]
  END_rules
}
EOF

echo "[$TIMESTAMP] ✓ Updated HTTP vhost configuration" >> "$LOG_FILE"

# ============================================
# 4. FIX HTTPS VHOST (Port 443)
# ============================================
echo "[$TIMESTAMP] Fixing HTTPS vhost..." >> "$LOG_FILE"

HTTPS_VHOST="/usr/local/lsws/conf/webuzo_vh/innoversebd.bdix.cloud-443/vhost.conf"
sudo cp "$HTTPS_VHOST" "$BACKUP_DIR/vhost-443.conf.$(date +%Y%m%d_%H%M%S)"

sudo tee "$HTTPS_VHOST" > /dev/null << 'EOF'
docRoot                   /home/sailo/innoverse/innoverse
enableGzip                1

errorlog /home/sailo/innoverse/logs/litespeed-error.log {
  useServer               0
  logLevel                ERROR
  rollingSize             10M
  compressArchive         1
}

accesslog /home/sailo/innoverse/logs/litespeed-access.log {
  useServer               0
  logFormat               %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"
  logHeaders              5
  rollingSize             10M
  keepDays                30
  compressArchive         1
}

index  {
  useServer               0
  autoIndex               0
}

# SECURITY - Block malicious patterns
context exp:^.*\.(ssh|env|git|aws|vscode|key|pwd) {
  allowBrowse             0
  rewrite  {
    enable                1
    rules                 RewriteRule .* - [F,L]
  }
}

context exp:^.*(phpinfo|wp-admin|setup-config|schema\.rb|credentials|docker-compose|config\.json|secrets\.json|service\.pwd|sftp\.json) {
  allowBrowse             0
  rewrite  {
    enable                1
    rules                 RewriteRule .* - [F,L]
  }
}

# STATIC FILES
context /static/ {
  type                    null
  location                /home/sailo/innoverse/innoverse/static/
  allowBrowse             1
  enableExpires           1
  expiresByType           */*=A2592000
  extraHeaders            <<<END_extraHeaders
Cache-Control public, immutable
  END_extraHeaders
  addDefaultCharset       off
}

context /media/ {
  type                    null
  location                /home/sailo/innoverse/innoverse/media/
  allowBrowse             1
  enableExpires           1
  expiresByType           */*=A2592000
  extraHeaders            <<<END_extraHeaders
Cache-Control public
  END_extraHeaders
  addDefaultCharset       off
}

# DJANGO APPLICATION
context / {
  type                    proxy
  handler                 gunicorn_innoverse
  addDefaultCharset       off
  extraHeaders            <<<END_extraHeaders
X-Forwarded-Proto https
X-Forwarded-For %{REMOTE_ADDR}e
X-Real-IP %{REMOTE_ADDR}e
  END_extraHeaders
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
}
EOF

echo "[$TIMESTAMP] ✓ Updated HTTPS vhost configuration" >> "$LOG_FILE"

# ============================================
# 5. VERIFY SSL CERTIFICATE FILES
# ============================================
echo "[$TIMESTAMP] Verifying SSL certificate files..." >> "$LOG_FILE"

if [ -f "/etc/letsencrypt/live/innoversebd.bdix.cloud/fullchain.pem" ]; then
    echo "[$TIMESTAMP] ✓ SSL certificate exists" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ⚠ WARNING: SSL certificate not found!" >> "$LOG_FILE"
fi

# ============================================
# 6. RESTART LITESPEED
# ============================================
echo "[$TIMESTAMP] Restarting LiteSpeed..." >> "$LOG_FILE"
sudo /usr/local/lsws/bin/lswsctrl restart >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] ✓ LiteSpeed restarted successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ✗ ERROR: LiteSpeed restart failed!" >> "$LOG_FILE"
fi

# ============================================
# 7. VERIFY CONFIGURATIONS
# ============================================
echo "[$TIMESTAMP] Verifying configurations..." >> "$LOG_FILE"

# Check if HTTPS is working
sleep 5
if curl -ks https://innoversebd.bdix.cloud/api/ -o /dev/null -w "%{http_code}" | grep -q "200\|404"; then
    echo "[$TIMESTAMP] ✓ HTTPS is working" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ⚠ WARNING: HTTPS may not be working properly" >> "$LOG_FILE"
fi

# Check DNS resolution
if ! grep -q "127.0.0.1 innoversebd.bdix.cloud" /etc/hosts; then
    echo "[$TIMESTAMP] ✓ DNS resolution is correct" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ✗ ERROR: Localhost entry still in /etc/hosts!" >> "$LOG_FILE"
fi

echo "[$TIMESTAMP] Configuration fixes completed!" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Send notification (optional - requires mail setup)
echo "Webuzo configs fixed at $TIMESTAMP" | mail -s "LiteSpeed Config Fixed" abdullahsami4103@gmail.com