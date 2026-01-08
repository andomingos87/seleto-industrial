import { NextResponse } from "next/server"

/**
 * Health check endpoint for Fly.io and monitoring
 * Returns basic health status of the admin panel
 */
export async function GET() {
  const healthCheck = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || "1.0.0",
    environment: process.env.NODE_ENV || "development",
    uptime: process.uptime(),
  }

  return NextResponse.json(healthCheck, {
    status: 200,
    headers: {
      "Cache-Control": "no-cache, no-store, must-revalidate",
    },
  })
}
