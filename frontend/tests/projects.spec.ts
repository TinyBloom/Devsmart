import { test, expect } from '@playwright/test';

test.describe('Project Management', () => {
  let projectName: string;
  let projectId: string;

  test.beforeEach(async ({ request }) => {
    projectName = `test-project-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const response = await request.post('/api/projects', {
      data: { name: projectName, description: 'Test project description' }
    });
    expect(response.ok()).toBeTruthy();
    const project = await response.json();
    projectId = project.id;
  });

  test.afterEach(async ({ request }) => {
    await request.delete(`/api/projects/${projectName}`).catch(() => {});
  });

  test('should create a new project', async ({ request }) => {
    const response = await request.get(`/api/projects/${projectName}`);
    expect(response.ok()).toBeTruthy();
    const project = await response.json();
    expect(project.name).toBe(projectName);
    expect(project.description).toBe('Test project description');
    expect(project.current_phase).toBe('prd');
    expect(project.prd_version).toBe(0);
  });

  test('should get project list', async ({ request }) => {
    const response = await request.get('/api/projects');
    expect(response.ok()).toBeTruthy();
    const projects = await response.json();
    expect(Array.isArray(projects)).toBe(true);
    const testProject = projects.find((p: any) => p.name === projectName);
    expect(testProject).toBeDefined();
  });

  test('should get project by name', async ({ request }) => {
    const response = await request.get(`/api/projects/${projectName}`);
    expect(response.ok()).toBeTruthy();
    const project = await response.json();
    expect(project.name).toBe(projectName);
  });

  test('should get project by ID', async ({ request }) => {
    const response = await request.get(`/api/projects/${projectId}`);
    expect(response.ok()).toBeTruthy();
    const project = await response.json();
    expect(project.id).toBe(projectId);
    expect(project.name).toBe(projectName);
  });

  test('should return 404 for non-existent project', async ({ request }) => {
    const response = await request.get('/api/projects/non-existent-project-xyz');
    expect(response.status()).toBe(404);
  });

  test('should update project', async ({ request }) => {
    const response = await request.put(`/api/projects/${projectName}`, {
      data: { description: 'Updated description' }
    });

    expect(response.ok()).toBeTruthy();
    const project = await response.json();
    expect(project.description).toBe('Updated description');
  });

  test('should delete project', async ({ request }) => {
    const response = await request.delete(`/api/projects/${projectName}`);
    expect(response.ok()).toBeTruthy();

    const getResponse = await request.get(`/api/projects/${projectName}`);
    expect(getResponse.status()).toBe(404);
  });
});

test.describe('Project Name Validation', () => {
  test('should reject project name with special characters', async ({ request }) => {
    const response = await request.post('/api/projects', {
      data: { name: 'test@project' }
    });
    expect(response.status()).toBe(422);
  });

  test('should reject project name too short', async ({ request }) => {
    const response = await request.post('/api/projects', {
      data: { name: 'ab' }
    });
    expect(response.status()).toBe(422);
  });

  test('should reject duplicate project name', async ({ request }) => {
    const name = 'duplicate-test';
    await request.post('/api/projects', { data: { name } });
    
    const response = await request.post('/api/projects', { data: { name } });
    expect(response.status()).toBe(400);
  });
});