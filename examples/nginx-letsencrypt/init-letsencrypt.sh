#!/bin/bash

# init-letsencrypt.sh - Initialize Let's Encrypt certificates for nginx
#
# This script:
# 1. Creates dummy certificates for initial nginx startup
# 2. Starts nginx
# 3. Requests real certificates from Let's Encrypt
# 4. Reloads nginx with real certificates
#
# Based on: https://github.com/wmnnd/nginx-certbot

set -e

# Configuration
domains=(doc.example.com)
rsa_key_size=4096
data_path="./certbot"
email="" # Adding a valid email is strongly recommended
staging=0 # Set to 1 if you're testing your setup to avoid rate limits

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Let's Encrypt Certificate Initialization ===${NC}"
echo ""

# Check if domain is configured
if [ "${domains[0]}" = "doc.example.com" ]; then
    echo -e "${RED}ERROR: Please update the 'domains' variable in this script!${NC}"
    echo -e "${YELLOW}Change 'doc.example.com' to your actual domain.${NC}"
    exit 1
fi

# Prompt for email if not set
if [ -z "$email" ]; then
    echo -e "${YELLOW}No email address configured.${NC}"
    echo -n "Enter email address for Let's Encrypt notifications: "
    read email
    echo ""
fi

# Confirm configuration
echo "Domain(s): ${domains[@]}"
echo "Email: $email"
echo "Data path: $data_path"
echo "RSA key size: $rsa_key_size"
echo "Staging mode: $([ $staging -eq 1 ] && echo 'enabled' || echo 'disabled')"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Check if certificates already exist
if [ -d "$data_path/conf/live/${domains[0]}" ]; then
    echo -e "${YELLOW}Existing certificates found for ${domains[0]}.${NC}"
    read -p "Replace existing certificates? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates."
        exit 0
    fi
fi

# Download recommended TLS parameters if not present
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
    echo -e "${GREEN}### Downloading recommended TLS parameters...${NC}"
    mkdir -p "$data_path/conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
    echo ""
fi

# Create dummy certificate for initial nginx startup
echo -e "${GREEN}### Creating dummy certificate for ${domains[0]}...${NC}"
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo ""

# Start nginx with dummy certificate
echo -e "${GREEN}### Starting nginx...${NC}"
docker-compose up --force-recreate -d nginx
echo ""

# Delete dummy certificate
echo -e "${GREEN}### Deleting dummy certificate for ${domains[0]}...${NC}"
docker-compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/${domains[0]} && \
  rm -rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo ""

# Request Let's Encrypt certificate
echo -e "${GREEN}### Requesting Let's Encrypt certificate for ${domains[0]}...${NC}"

# Join domains with -d flag
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Enable staging mode if requested
if [ $staging != "0" ]; then
    staging_arg="--staging"
else
    staging_arg=""
fi

docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo ""

# Reload nginx to use real certificate
echo -e "${GREEN}### Reloading nginx...${NC}"
docker-compose exec nginx nginx -s reload
echo ""

echo -e "${GREEN}=== Certificate initialization complete! ===${NC}"
echo ""
echo "Your pdfa-service is now running with Let's Encrypt SSL/TLS certificates."
echo "Certificates will be automatically renewed by the certbot container."
echo ""
echo "Access your service at: https://${domains[0]}"
echo ""
echo -e "${YELLOW}Note: If you used staging mode, you'll see a browser warning.${NC}"
echo -e "${YELLOW}Run this script again with staging=0 to get production certificates.${NC}"
