import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { KeyboardEvent } from 'react';
import {
  FolderKanban,
  LoaderCircle,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Sparkles,
} from 'lucide-react';
import type { Project, OnboardingData, ProjectType } from '../types';
import { projectApi } from '../services/api';
import { ProjectList } from '../components/ProjectList';
import { OnboardingWizard } from '../components/OnboardingWizard';

type ActiveView = 'list' | 'create';

type NavItem = {
  id: ActiveView;
  label: string;
  icon: 'create' | 'list';
};

export function HomePage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<ActiveView>('list');

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const data = await projectApi.getProjects(searchQuery);
      setProjects(data);
    } catch (error) {
      console.error('加载项目失败:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreateProject = async (
    onboardingData: OnboardingData,
    projectType: ProjectType,
    projectName: string,
    sourcePath?: string,
  ) => {
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
      await loadProjects();
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
      await loadProjects();
    } catch (error) {
      console.error('删除项目失败:', error);
    }
  };

  const navItems: NavItem[] = [
    { id: 'create', label: '创建新项目', icon: 'create' },
    { id: 'list', label: '项目列表', icon: 'list' },
  ];

  const handleNavKeyDown = (event: KeyboardEvent<HTMLButtonElement>, item: NavItem) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setActiveView(item.id);
    }
  };

  const renderIcon = (iconName: NavItem['icon']) => {
    if (iconName === 'create') {
      return <Plus size={18} strokeWidth={1.8} aria-hidden="true" />;
    }
    return <FolderKanban size={18} strokeWidth={1.8} aria-hidden="true" />;
  };

  return (
    <div className={`app-shell ${sidebarOpen ? '' : 'sidebar-is-collapsed'}`}>
      <aside className={`app-sidebar ${sidebarOpen ? 'is-open' : 'is-collapsed'}`}>
        <div className="sidebar-brand">
          <button
            className="brand-mark"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
            title={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
          >
            <Sparkles size={20} strokeWidth={1.8} aria-hidden="true" />
          </button>
          {sidebarOpen && (
            <div>
              <div className="brand-name">DevSmart</div>
              <div className="brand-caption">AI product workspace</div>
            </div>
          )}
        </div>

        <nav className="sidebar-nav" aria-label="主导航">
          {sidebarOpen && <div className="sidebar-label">工作区</div>}
          <div className="sidebar-nav-list">
            {navItems.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveView(item.id)}
                onKeyDown={(event) => handleNavKeyDown(event, item)}
                className={`sidebar-nav-item ${activeView === item.id ? 'is-active' : ''}`}
                aria-label={item.label}
                title={!sidebarOpen ? item.label : undefined}
              >
                {renderIcon(item.icon)}
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            ))}
          </div>
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="sidebar-collapse-button"
            aria-label={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
            title={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
          >
            {sidebarOpen ? <PanelLeftClose size={18} aria-hidden="true" /> : <PanelLeftOpen size={18} aria-hidden="true" />}
            {sidebarOpen && <span>收起侧边栏</span>}
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <div>
            <div className="topbar-overline">AI development workspace</div>
            <h1 className="topbar-title">从想法到可交付 PRD</h1>
          </div>
          <div className="topbar-status" aria-label="工作区已就绪">
            <span className="status-dot" aria-hidden="true" />
            <span>工作区已就绪</span>
          </div>
        </header>

        <main id="main-content" className="app-content">
          <div className="page-container">
            {activeView === 'list' ? (
              <>
                <div className="page-intro">
                  <div>
                    <div className="page-eyebrow">Projects</div>
                    <h2 className="page-heading">你的项目</h2>
                    <p className="page-description">管理需求、对话与 PRD 产出，让每个想法都有清晰的下一步。</p>
                  </div>
                  <button type="button" className="primary-button" onClick={() => setActiveView('create')}>
                    <Plus size={17} aria-hidden="true" />
                    创建新项目
                  </button>
                </div>

                {loading ? (
                  <div className="page-loading">
                    <div className="loading-inline">
                      <LoaderCircle size={20} className="loading-icon" aria-hidden="true" />
                      <span>正在加载项目...</span>
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
                )}
              </>
            ) : (
              <div className="onboarding-shell">
                <OnboardingWizard
                  onComplete={handleCreateProject}
                  onCancel={() => setActiveView('list')}
                  embedded
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
