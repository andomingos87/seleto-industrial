import { Page, Route } from '@playwright/test';

/**
 * Mock data for API responses.
 */
export const mockData = {
  status: {
    timestamp: new Date().toISOString(),
    agent_status: 'active',
    integrations: {
      whatsapp: { status: 'ok', latency_ms: 120 },
      supabase: { status: 'ok', latency_ms: 45 },
      openai: { status: 'ok', latency_ms: 800 },
      piperun: { status: 'ok', latency_ms: 150 },
      chatwoot: { status: 'ok', latency_ms: 200 },
    },
  },

  agentStatus: {
    status: 'active',
    paused_phones: ['5511999999999'],
    total_paused: 1,
  },

  businessHours: {
    timezone: 'America/Sao_Paulo',
    schedule: {
      monday: { start: '08:00', end: '18:00' },
      tuesday: { start: '08:00', end: '18:00' },
      wednesday: { start: '08:00', end: '18:00' },
      thursday: { start: '08:00', end: '18:00' },
      friday: { start: '08:00', end: '18:00' },
      saturday: null,
      sunday: null,
    },
    current_status: {
      is_business_hours: true,
      current_time: '10:30',
      timezone: 'America/Sao_Paulo',
    },
  },

  leads: {
    items: [
      {
        id: '1',
        phone: '5511999999999',
        name: 'João Silva',
        email: 'joao@empresa.com',
        city: 'São Paulo',
        uf: 'SP',
        product: 'FBM-100',
        volume: '500L/dia',
        urgency: 'alta',
        knows_seleto: true,
        temperature: 'quente',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-05T15:30:00Z',
      },
      {
        id: '2',
        phone: '5521988888888',
        name: 'Maria Santos',
        email: 'maria@empresa.com',
        city: 'Rio de Janeiro',
        uf: 'RJ',
        product: 'FB-300',
        volume: '1000L/dia',
        urgency: 'média',
        knows_seleto: false,
        temperature: 'morno',
        created_at: '2024-01-02T14:00:00Z',
        updated_at: '2024-01-04T09:00:00Z',
      },
      {
        id: '3',
        phone: '5531977777777',
        name: 'Pedro Oliveira',
        email: null,
        city: 'Belo Horizonte',
        uf: 'MG',
        product: null,
        volume: null,
        urgency: null,
        knows_seleto: null,
        temperature: 'frio',
        created_at: '2024-01-03T08:00:00Z',
        updated_at: '2024-01-03T08:00:00Z',
      },
    ],
    total: 3,
    page: 1,
    limit: 20,
  },

  leadDetail: {
    id: '1',
    phone: '5511999999999',
    name: 'João Silva',
    email: 'joao@empresa.com',
    city: 'São Paulo',
    uf: 'SP',
    product: 'FBM-100',
    volume: '500L/dia',
    urgency: 'alta',
    knows_seleto: true,
    temperature: 'quente',
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-05T15:30:00Z',
  },

  conversation: {
    messages: [
      {
        id: 'msg1',
        role: 'user',
        content: 'Olá, gostaria de saber mais sobre a FBM-100',
        timestamp: '2024-01-01T10:00:00Z',
      },
      {
        id: 'msg2',
        role: 'assistant',
        content: 'Olá! Claro, a FBM-100 é nossa misturadora de alta performance. Qual o volume de produção que você precisa?',
        timestamp: '2024-01-01T10:00:30Z',
      },
      {
        id: 'msg3',
        role: 'user',
        content: 'Preciso processar cerca de 500 litros por dia',
        timestamp: '2024-01-01T10:01:00Z',
      },
      {
        id: 'msg4',
        role: 'assistant',
        content: 'Perfeito! A FBM-100 atende muito bem essa demanda. Você já conhece a Seleto Industrial?',
        timestamp: '2024-01-01T10:01:30Z',
      },
    ],
    total: 4,
  },
};

/**
 * Setup API mocks for all admin endpoints.
 */
export async function setupApiMocks(page: Page) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Mock status endpoint
  await page.route(`${apiUrl}/api/admin/status`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.status),
    });
  });

  // Mock agent status endpoint
  await page.route(`${apiUrl}/api/admin/agent/status`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.agentStatus),
    });
  });

  // Mock pause endpoint
  await page.route(`${apiUrl}/api/admin/agent/pause`, async (route: Route) => {
    const body = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: `Agent paused for ${body?.phone || 'all'}`,
        phone: body?.phone,
      }),
    });
  });

  // Mock resume endpoint
  await page.route(`${apiUrl}/api/admin/agent/resume`, async (route: Route) => {
    const body = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: `Agent resumed for ${body?.phone || 'all'}`,
        phone: body?.phone,
      }),
    });
  });

  // Mock reload prompt endpoint
  await page.route(`${apiUrl}/api/admin/agent/reload-prompt`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'System prompt reloaded successfully',
      }),
    });
  });

  // Mock business hours GET endpoint
  await page.route(`${apiUrl}/api/admin/config/business-hours`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.businessHours),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockData.businessHours),
      });
    }
  });

  // Mock leads list endpoint
  await page.route(`${apiUrl}/api/admin/leads?*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.leads),
    });
  });

  await page.route(`${apiUrl}/api/admin/leads`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.leads),
    });
  });

  // Mock lead detail endpoint
  await page.route(`${apiUrl}/api/admin/leads/5511999999999`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.leadDetail),
    });
  });

  // Mock conversation endpoint
  await page.route(`${apiUrl}/api/admin/leads/*/conversation*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockData.conversation),
    });
  });
}

/**
 * Setup mock for a specific endpoint with custom response.
 */
export async function mockEndpoint(
  page: Page,
  endpoint: string,
  response: object,
  status = 200
) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  await page.route(`${apiUrl}${endpoint}`, async (route: Route) => {
    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}
