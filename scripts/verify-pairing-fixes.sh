#!/bin/bash
# Verification script for pairing fixes in Docker
# This script verifies both QR code library bundling and i18n translation fixes

set -e

echo "🔍 Verifying Pairing Fixes in Docker..."
echo ""

# Check if service is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Service is not running on http://localhost:8000"
    echo "   Please run: docker compose up -d"
    exit 1
fi

echo "✅ Service is running"
echo ""

# Verify QR code library is bundled locally
echo "📦 Checking QR Code Library..."
QR_SIZE=$(curl -s http://localhost:8000/static/js/vendor/qrcode.min.js | wc -c)
if [ "$QR_SIZE" -gt 15000 ]; then
    echo "✅ QR code library is bundled locally (${QR_SIZE} bytes)"
else
    echo "❌ QR code library not found or too small"
    exit 1
fi

# Verify HTML references local library
echo ""
echo "🔗 Checking HTML references local library..."
if curl -s http://localhost:8000/en | grep -q '/static/js/vendor/qrcode.min.js'; then
    echo "✅ HTML references local QR code library"
else
    echo "❌ HTML still references CDN"
    exit 1
fi

# Verify i18n fix is applied
echo ""
echo "🌍 Checking i18n Translation Fix..."
if curl -s http://localhost:8000/static/js/camera/MobilePairingManager.js | grep -q 'window.applyTranslations'; then
    echo "✅ i18n fix is applied (calls window.applyTranslations)"
else
    echo "❌ i18n fix not found"
    exit 1
fi

# Verify translations are available
echo ""
echo "📖 Checking Translations..."
TRANSLATIONS=$(curl -s http://localhost:8000/static/js/i18n/translations.js | grep -c "camera.pairing.waiting")
if [ "$TRANSLATIONS" -eq 4 ]; then
    echo "✅ Translations available for all 4 languages (EN, DE, ES, FR)"
    echo ""
    echo "   🇬🇧 EN: Waiting for mobile..."
    echo "   🇩🇪 DE: Warte auf Mobilgerät..."
    echo "   🇪🇸 ES: Esperando móvil..."
    echo "   🇫🇷 FR: En attente du mobile..."
else
    echo "❌ Expected 4 translations, found $TRANSLATIONS"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL FIXES VERIFIED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  ✅ QR code library bundled locally (no CDN dependency)"
echo "  ✅ i18n translation fix applied (dynamic translation)"
echo "  ✅ All 4 language translations available"
echo ""
