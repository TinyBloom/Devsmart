/**
 * HomePage Component
 * 主页面，包含项目列表和 LLM 设置入口
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Project } from '../types';
import { projectApi } from '../services/api';
import { ProjectList } from '../components/ProjectList';
import { ProjectForm } from '../components/ProjectForm';
import { LLMSettings } from '../components/LLMSettings';

export function HomePage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, [searchQuery]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await projectApi.getProjects(searchQuery);
      setProjects(data);
    } catch (error) {
      console.error('加载项目失败:', error);
    }
    setLoading(false);
  };

  const handleCreateProject = async (name: string, description?: string) => {
    try {
      await projectApi.createProject(name, description);
      setShowCreateForm(false);
      loadProjects();
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建项目失败');
    }
  };

  const handleSelectProject = async (project: Project) => {
    // 恢复项目上下文并跳转到项目详情页
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

  return (
    <div className="home-page">
      {/* 头部 */}
      <header className="header">
        <div className="header-left">
          <h1 className="logo">DevSmart</h1>
          <span className="subtitle">LLM驱动的软件开发平台</span>
        </div>
        <div className="header-right">
          <button className="settings-btn" onClick={() => setShowSettings(true)}>
            LLM 设置
          </button>
        </div>
      </header>

      {/* 主内容 */}
      <main className="main-content">
        {/* 操作栏 */}
        <div className="action-bar">
          <button className="create-btn" onClick={() => setShowCreateForm(true)}>
            + 新建项目
          </button>
        </div>

        {/* 项目列表 */}
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <ProjectList
            projects={projects}
            onSelectProject={handleSelectProject}
            onDeleteProject={handleDeleteProject}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
        )}
      </main>

      {/* 创建项目弹窗 */}
      {showCreateForm && (
        <ProjectForm
          onSubmit={handleCreateProject}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* LLM 设置弹窗 */}
      {showSettings && (
        <LLMSettings onClose={() => setShowSettings(false)} />
      )}

      <style>{`
        .home-page {
          min-height: 100vh;
          background: #f5f5f5;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 40px;
          background: white;
          border-bottom: 1px solid #ddd;
        }

        .header-left {
          display: flex;
          align-items: baseline;
          gap: 15px;
        }

        .logo {
          font-size: 24px;
          font-weight: 700;
          color: #333;
        }

        .subtitle {
          font-size: 14px;
          color: #888;
        }

        .header-right {
          display: flex;
          gap: 10px;
        }

        .settings-btn {
          padding: 10px 20px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }

        .main-content {
          padding: 40px;
        }

        .action-bar {
          margin-bottom: 20px;
        }

        .create-btn {
          padding: 12px 24px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 15px;
          font-weight: 600;
        }

        .create-btn:hover {
          background: #45a049;
        }

        .loading {
          text-align: center;
          padding: 40px;
          color: #888;
        }
      `}</style>
    </div>
  );
}