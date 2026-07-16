import { ArrowUpRight, FolderOpen, Search, Trash2 } from 'lucide-react';
import type { Project } from '../types';

interface ProjectListProps {
  projects: Project[];
  onSelectProject: (project: Project) => void;
  onDeleteProject: (name: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function ProjectList({
  projects,
  onSelectProject,
  onDeleteProject,
  searchQuery,
  onSearchChange,
}: ProjectListProps) {
  const getPhaseClass = (phase: string) => {
    if (['prd', 'tech', 'code', 'test', 'deploy'].includes(phase)) {
      return `phase-${phase}`;
    }
    return 'phase-default';
  };

  const getPhaseLabel = (phase: string) => {
    switch (phase) {
      case 'prd':
        return 'PRD';
      case 'tech':
        return '技术设计';
      case 'code':
        return '开发';
      case 'test':
        return '测试';
      case 'deploy':
        return '部署';
      default:
        return phase;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      }).format(date);
    } catch {
      return dateString;
    }
  };

  return (
    <section className="project-list" aria-label="项目列表">
      <div className="project-list-toolbar">
        <p className="project-count">共 {projects.length} 个项目</p>
        <div className="search-field">
          <Search size={17} strokeWidth={1.8} aria-hidden="true" />
          <label htmlFor="project-search" className="sr-only">搜索项目</label>
          <input
            id="project-search"
            type="search"
            name="project-search"
            placeholder="按名称搜索项目"
            value={searchQuery}
            onChange={(event) => onSearchChange(event.target.value)}
            spellCheck={false}
            aria-label="搜索项目"
          />
        </div>
      </div>

      <div className="project-grid">
        {projects.length === 0 ? (
          <div className="project-empty">
            <div className="project-empty-icon">
              <FolderOpen size={24} strokeWidth={1.7} aria-hidden="true" />
            </div>
            <strong>{searchQuery ? '没有找到匹配项目' : '还没有项目'}</strong>
            <p>{searchQuery ? '尝试更换关键词，或清空搜索条件。' : '点击“创建新项目”，开始梳理你的第一个想法。'}</p>
          </div>
        ) : (
          projects.map((project) => (
            <article key={project.id} className="project-card">
              <button
                type="button"
                className="project-card-main"
                onClick={() => onSelectProject(project)}
                aria-label={`打开项目 ${project.name}`}
              >
                <div className="project-card-heading">
                  <h3>{project.name}</h3>
                </div>

                <p className="project-card-description">
                  {project.description || '暂无项目描述'}
                </p>

                <div className="project-card-meta">
                  <span className={`phase-badge ${getPhaseClass(project.current_phase)}`}>
                    {getPhaseLabel(project.current_phase)}
                  </span>
                  <span className="project-version">PRD v{project.prd_version}</span>
                </div>

                <div className="project-card-footer flex items-center justify-between gap-3">
                  <span>更新于 {formatDate(project.updated_at)}</span>
                  <ArrowUpRight size={15} strokeWidth={1.8} aria-hidden="true" />
                </div>
              </button>

              <button
                type="button"
                onClick={() => onDeleteProject(project.name)}
                className="project-delete"
                aria-label={`删除项目 ${project.name}`}
                title="删除项目"
              >
                <Trash2 size={16} strokeWidth={1.8} aria-hidden="true" />
              </button>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
