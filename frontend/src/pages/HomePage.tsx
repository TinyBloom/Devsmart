/**
 * HomePage Component
 * 主页面，左右结构布局
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Project, OnboardingData, ProjectType } from '../types';
import { projectApi } from '../services/api';
import { ProjectList } from '../components/ProjectList';
import { OnboardingWizard } from '../components/OnboardingWizard';

type ActiveView = 'list' | 'create';

export function HomePage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<ActiveView>('list');

  useEffect(() => {
    loadProjects();
  }, [searchQuery]);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const data = await projectApi.getProjects(searchQuery);
      setProjects(data);
    } catch (error) {
      console.error('加载项目失败:', error);
    }
    setLoading(false);
  }, [searchQuery]);

  const handleCreateProject = async (onboardingData: OnboardingData, projectType: ProjectType, projectName: string, sourcePath?: string) => {
    try {
      const description = onboardingData.requirement_description.substring(0, 200);
      await projectApi.createProject({
        name: projectName,
        description,
        project_type: projectType,
        source_path: sourcePath,
        onboarding_data: onboardingData,
      });
      setActiveView('list');
      loadProjects();
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建项目失败');
    }
  };

  const handleSelectProject = async (project: Project) => {
    try {
      const context = await projectApi.getProject(project.name);
      navigate(`/projects/${context.id}`);
    } catch (error) {
      console.error('恢复项目失败:', error);
    }
  };

  const handleDeleteProject = async (name: string) => {
    if (!confirm(`确定删除项目 "${name}"？此操作不可撤销。`)) {
      return;
    }
    try {
      await projectApi.deleteProject(name);
      loadProjects();
    } catch (error) {
      console.error('删除项目失败:', error);
    }
  };

  const navItems = [
    { id: 'create', label: '创建新项目', icon: 'create' },
    { id: 'list', label: '项目列表', icon: 'list' },
  ];

  const handleNavKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      (e.target as HTMLButtonElement).click();
    }
  };

  const renderIcon = (iconName: string) => {
    const icons = {
      create: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      ),
      list: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
      ),
    };
    return icons[iconName as keyof typeof icons] || icons.list;
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* 左侧导航栏 */}
      <aside
        className={`flex flex-col bg-white border-r border-gray-200 flex-shrink-0 transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'w-[15%]' : 'w-16'
        }`}
      >
        {/* 侧边栏头部 */}
        <div className="flex items-center justify-center p-4 border-b border-gray-200">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex items-center gap-3 w-full justify-center hover:bg-gray-50 rounded-lg p-2 transition-colors"
            aria-label={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
          >
            <div className="w-10 h-10 bg-[#2496ED] rounded-lg flex items-center justify-center">
              <span className="text-xl font-bold text-white">D</span>
            </div>
            {sidebarOpen && (
              <span className="text-xl font-bold text-gray-900">DevSmart</span>
            )}
          </button>
        </div>

        {/* 导航菜单 */}
        {sidebarOpen && (
          <nav className="flex-1 p-3 space-y-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id as ActiveView)}
                onKeyDown={handleNavKeyDown}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-[background-color,color] duration-200 focus-visible:ring-2 focus-visible:ring-[#2496ED] focus-visible:ring-offset-2 ${
                  activeView === item.id
                    ? 'bg-[#2496ED] text-white'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
                aria-label={item.label}
              >
                {renderIcon(item.icon)}
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
        )}

        {/* 收起状态：只显示图标按钮 */}
        {!sidebarOpen && (
          <nav className="flex-1 flex flex-col items-center justify-center p-3">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setSidebarOpen(true);
                  setActiveView(item.id as ActiveView);
                }}
                onKeyDown={handleNavKeyDown}
                className={`w-12 h-12 flex items-center justify-center rounded-lg transition-[background-color,color] duration-200 focus-visible:ring-2 focus-visible:ring-[#2496ED] focus-visible:ring-offset-2 ${
                  activeView === item.id
                    ? 'bg-[#2496ED] text-white'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
                aria-label={item.label}
                title={item.label}
              >
                {renderIcon(item.icon)}
              </button>
            ))}
          </nav>
        )}

        {/* 折叠按钮（仅展开时显示） */}
        {sidebarOpen && (
          <div className="p-3 border-t border-gray-200">
            <button
              onClick={() => setSidebarOpen(false)}
              className="w-full flex items-center justify-center gap-2 py-3 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
              aria-label="收起侧边栏"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-medium">收起侧边栏</span>
            </button>
          </div>
        )}
      </aside>

      {/* 右侧内容区 */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* 顶部标题栏 */}
        <header className="bg-white border-b border-gray-200 h-[8%] flex items-center justify-center">
          <h1 className="text-xl md:text-2xl font-bold text-gray-900">
            DevSmart <span className="text-[#2496ED] font-normal">LLM驱动的软件开发平台</span>
          </h1>
        </header>

        {/* 主体内容区 */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className={`p-6 md:p-8 mx-auto h-full ${sidebarOpen ? 'w-[80%]' : 'w-[90%]'}`}>
            {activeView === 'list' ? (
              loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex items-center gap-3 text-gray-500">
                    <svg className="w-6 h-6 animate-spin text-[#2496ED]" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-lg">加载中…</span>
                  </div>
                </div>
              ) : (
                <ProjectList
                  projects={projects}
                  onSelectProject={handleSelectProject}
                  onDeleteProject={handleDeleteProject}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                />
              )
            ) : (
              <OnboardingWizard
                onComplete={handleCreateProject}
                onCancel={() => setActiveView('list')}
                embedded
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}