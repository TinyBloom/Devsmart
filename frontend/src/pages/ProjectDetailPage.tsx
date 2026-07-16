import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  FileText,
  LoaderCircle,
  MessageSquareText,
  PackageOpen,
} from 'lucide-react';
import type { Project } from '../types';
import { ConversationPanel } from '../components/ConversationPanel';
import { MarkdownRenderer } from '../components/MarkdownRenderer';

export function ProjectDetailPage() {
  const navigate = useNavigate();
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
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
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
      <div className="page-loading">
        <div className="loading-inline">
          <LoaderCircle size={20} className="loading-icon" aria-hidden="true" />
          <span>正在加载项目...</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page-error">
        <div className="empty-prd">
          <PackageOpen size={32} strokeWidth={1.6} aria-hidden="true" />
          <h3>项目不存在</h3>
          <button type="button" className="secondary-button" onClick={() => navigate('/')}>
            返回项目列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="project-detail-page">
      <header className="project-header">
        <div className="detail-header-top">
          <button type="button" className="back-link" onClick={() => navigate('/')}>
            <ArrowLeft size={17} strokeWidth={1.8} aria-hidden="true" />
            所有项目
          </button>
          <button
            type="button"
            className="download-btn"
            onClick={downloadPackage}
            disabled={downloading}
          >
            {downloading ? <LoaderCircle size={16} className="loading-icon" aria-hidden="true" /> : <Download size={16} aria-hidden="true" />}
            {downloading ? '下载中...' : '下载 Package'}
          </button>
        </div>

        <div className="header-content">
          <div className="header-info">
            <div className="project-kicker">Project workspace</div>
            <h1>{project.name}</h1>
            <p className="project-description">{project.description || '这个项目还没有添加描述。'}</p>
            <div className="project-meta">
              <span>当前阶段：{project.current_phase}</span>
              <span>PRD 版本：v{project.prd_version}</span>
              <span>创建于：{new Date(project.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="项目内容">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'conversation'}
          className={activeTab === 'conversation' ? 'active' : ''}
          onClick={() => setActiveTab('conversation')}
        >
          <MessageSquareText size={16} strokeWidth={1.8} aria-hidden="true" />
          对话
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'prd'}
          className={activeTab === 'prd' ? 'active' : ''}
          onClick={() => setActiveTab('prd')}
        >
          <FileText size={16} strokeWidth={1.8} aria-hidden="true" />
          PRD
        </button>
      </div>

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
              <div className="loading-indicator">
                <div className="loading-inline">
                  <LoaderCircle size={20} className="loading-icon" aria-hidden="true" />
                  <span>加载 PRD 中...</span>
                </div>
              </div>
            ) : project.prd_version > 0 ? (
              <div className="prd-content-wrapper">
                <div className="prd-header">
                  <h2>产品需求文档 · v{project.prd_version}</h2>
                </div>
                <MarkdownRenderer content={prdContent} />
              </div>
            ) : (
              <div className="empty-prd">
                <PackageOpen size={36} strokeWidth={1.5} aria-hidden="true" />
                <h3>尚未生成 PRD</h3>
                <p>先在对话中完成需求梳理，再生成第一版产品需求文档。</p>
                <button type="button" className="go-to-conversation-btn" onClick={() => setActiveTab('conversation')}>
                  <MessageSquareText size={16} aria-hidden="true" />
                  前往对话
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
