/**
 * ProjectDetailPage Component
 * 项目详情页面，包含对话界面和 PRD 查看
 */

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import type { Project } from '../types';
import { ConversationPanel } from '../components/ConversationPanel';
import { MarkdownRenderer } from '../components/MarkdownRenderer';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'conversation' | 'prd'>('conversation');
  const [downloading, setDownloading] = useState(false);
  const [prdContent, setPrdContent] = useState('');
  const [prdLoading, setPrdLoading] = useState(false);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async (): Promise<void> => {
    if (!projectId) return;

    try {
      const response = await fetch(`/api/projects/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setProject(data);
      }
    } catch (error) {
      console.error('加载项目失败:', error);
    }

    setLoading(false);
  };

  const downloadPackage = async () => {
    if (!projectId) return;

    try {
      setDownloading(true);
      const response = await fetch(`/api/projects/${projectId}/package`);
      
      if (!response.ok) {
        throw new Error('下载失败');
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'project.zip';
      
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) {
          filename = match[1];
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载失败，请稍后重试');
    } finally {
      setDownloading(false);
    }
  };

  const loadPrdContent = async () => {
    if (!projectId) return;

    try {
      setPrdLoading(true);
      const response = await fetch(`/api/projects/${projectId}/prd`);
      
      if (response.ok) {
        const data = await response.json();
        setPrdContent(data.content || '');
      }
    } catch (error) {
      console.error('加载 PRD 内容失败:', error);
    } finally {
      setPrdLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'prd' && project?.prd_version && project.prd_version > 0) {
      loadPrdContent();
    }
  }, [activeTab, projectId, project?.prd_version]);

  if (loading) {
    return (
      <div className="loading-page">
        <p>加载中...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="error-page">
        <p>项目不存在</p>
      </div>
    );
  }

  return (
    <div className="project-detail-page">
      {/* 项目信息头部 */}
      <div className="project-header">
        <div className="header-content">
          <div className="header-info">
            <h1>{project.name}</h1>
            <p className="project-description">{project.description}</p>
            <div className="project-meta">
              <span>当前阶段: {project.current_phase}</span>
              <span>PRD 版本: v{project.prd_version}</span>
              <span>创建时间: {new Date(project.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <button 
            className="download-btn" 
            onClick={downloadPackage}
            disabled={downloading}
          >
            {downloading ? '下载中...' : '下载 Package'}
          </button>
        </div>
      </div>

      {/* Tab切换 */}
      <div className="tabs">
        <button
          className={activeTab === 'conversation' ? 'active' : ''}
          onClick={() => setActiveTab('conversation')}
        >
          对话
        </button>
        <button
          className={activeTab === 'prd' ? 'active' : ''}
          onClick={() => setActiveTab('prd')}
        >
          PRD
        </button>
      </div>

      {/* 内容区域 */}
      <div className="content-area">
        {activeTab === 'conversation' && (
          <ConversationPanel
            projectId={projectId!}
            projectName={project.name}
            onPrdGenerated={async () => {
              await loadProject();
              setActiveTab('prd');
            }}
          />
        )}

        {activeTab === 'prd' && (
          <div className="prd-view">
            {prdLoading ? (
              <div className="loading-indicator">加载 PRD 中...</div>
            ) : project?.prd_version && project.prd_version > 0 ? (
              <div className="prd-content-wrapper">
                <div className="prd-header">
                  <h2>产品需求文档 (PRD) - v{project.prd_version}</h2>
                </div>
                <MarkdownRenderer content={prdContent} />
              </div>
            ) : (
              <div className="empty-prd">
                <h3>尚未生成 PRD</h3>
                <p>请先在对话中完成需求梳理，然后点击"生成 PRD"按钮</p>
                <button className="go-to-conversation-btn" onClick={() => setActiveTab('conversation')}>
                  前往对话
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        .project-detail-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
        }

        .project-header {
          padding: 20px;
          background: white;
          border-bottom: 1px solid #ddd;
        }

        .project-header h1 {
          margin-bottom: 10px;
          font-size: 24px;
        }

        .project-description {
          color: #666;
          margin-bottom: 15px;
        }

        .project-meta {
          display: flex;
          gap: 20px;
          font-size: 14px;
          color: #888;
        }

        .header-content {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .download-btn {
          padding: 12px 24px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: background 0.2s;
        }

        .download-btn:hover:not(:disabled) {
          background: #1976D2;
        }

        .download-btn:disabled {
          background: #90CAF9;
          cursor: not-allowed;
        }

        .tabs {
          display: flex;
          padding: 10px 20px;
          background: #f5f5f5;
        }

        .tabs button {
          padding: 10px 20px;
          border: none;
          background: transparent;
          cursor: pointer;
          font-size: 14px;
          color: #666;
        }

        .tabs button.active {
          background: white;
          border-radius: 8px;
          color: #2196F3;
        }

        .content-area {
          flex: 1;
          overflow: hidden;
        }

        .prd-view {
          padding: 20px;
          background: white;
          height: 100%;
          overflow-y: auto;
        }

        .prd-content-wrapper {
          max-width: 1000px;
          margin: 0 auto;
        }

        .prd-header {
          padding-bottom: 20px;
          border-bottom: 2px solid #eee;
          margin-bottom: 20px;
        }

        .prd-header h2 {
          margin: 0;
          font-size: 22px;
          color: #1a1a1a;
        }

        .empty-prd {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .empty-prd h3 {
          font-size: 20px;
          margin-bottom: 10px;
          color: #333;
        }

        .empty-prd p {
          margin-bottom: 20px;
        }

        .go-to-conversation-btn {
          padding: 12px 24px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: background 0.2s;
        }

        .go-to-conversation-btn:hover {
          background: #1976D2;
        }

        .loading-indicator {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #666;
          font-size: 16px;
        }

        .loading-page, .error-page {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
        }
      `}</style>
    </div>
  );
}