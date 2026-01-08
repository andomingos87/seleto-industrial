#!/bin/bash
# deploy.sh - Deploy Admin Panel to Fly.io
# Usage: ./scripts/deploy.sh

set -e

echo "🚀 Deploying Admin Panel to Fly.io..."
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run:"
    echo "   flyctl auth login"
    exit 1
fi

# Check for .env.production file
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production not found. Creating template..."
    cat > .env.production << EOF
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Backend API URL
API_URL=https://seleto-industrial.fly.dev
EOF
    echo "📝 Please edit .env.production with your credentials and run again."
    exit 1
fi

# Load environment variables
source .env.production

# Validate required variables
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project.supabase.co" ]; then
    echo "❌ SUPABASE_URL not configured in .env.production"
    exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ] || [ "$SUPABASE_ANON_KEY" = "your-anon-key" ]; then
    echo "❌ SUPABASE_ANON_KEY not configured in .env.production"
    exit 1
fi

if [ -z "$API_URL" ]; then
    echo "❌ API_URL not configured in .env.production"
    exit 1
fi

echo "📦 Building and deploying with:"
echo "   SUPABASE_URL: ${SUPABASE_URL:0:30}..."
echo "   API_URL: $API_URL"
echo ""

# Deploy with build args
flyctl deploy \
  --build-arg NEXT_PUBLIC_SUPABASE_URL="$SUPABASE_URL" \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
  -a seleto-admin-panel

echo ""
echo "✅ Deploy complete!"
echo ""

# Get app URL
APP_URL=$(flyctl status -a seleto-admin-panel --json 2>/dev/null | grep -o '"Hostname":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$APP_URL" ]; then
    echo "🔗 URL: https://$APP_URL"
else
    echo "🔗 URL: https://seleto-admin-panel.fly.dev"
fi

echo ""
echo "🏥 Checking health..."
sleep 5

# Check health endpoint
HEALTH_URL="https://seleto-admin-panel.fly.dev/api/health"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed!"
    curl -s "$HEALTH_URL" | python3 -m json.tool 2>/dev/null || curl -s "$HEALTH_URL"
else
    echo "⚠️  Health check returned status: $HTTP_STATUS"
    echo "   The app may still be starting up. Check logs with:"
    echo "   flyctl logs -a seleto-admin-panel"
fi

echo ""
echo "📊 View status: flyctl status -a seleto-admin-panel"
echo "📜 View logs: flyctl logs -a seleto-admin-panel"
echo "🌐 Open dashboard: flyctl dashboard -a seleto-admin-panel"
