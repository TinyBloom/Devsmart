/**
 * ProjectList Component
 * 项目列表展示组件
 */

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
  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'prd':
        return 'bg-emerald-100 text-emerald-700';
      case 'tech':
        return 'bg-[#E3F2FD] text-[#2496ED]';
      case 'code':
        return 'bg-amber-100 text-amber-700';
      case 'test':
        return 'bg-purple-100 text-purple-700';
      case 'deploy':
        return 'bg-orange-100 text-orange-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
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

  const handleCardKeyDown = (e: React.KeyboardEvent<HTMLDivElement>, project: Project) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelectProject(project);
    }
  };

  return (
    <div className="w-full">
      {/* 搜索框 */}
      <div className="mb-6">
        <label htmlFor="project-search" className="sr-only">搜索项目</label>
        <input
          id="project-search"
          type="text"
          name="project-search"
          placeholder="搜索项目…"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          spellCheck={false}
          className="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#2496ED] focus:border-[#2496ED] transition-[border-color,ring-color] duration-200"
          aria-label="搜索项目"
        />
      </div>

      {/* 项目列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {projects.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-24 text-gray-500">
            <p className="text-xl font-medium text-gray-900">暂无项目</p>
            <p className="text-gray-500 mt-2">点击左侧"创建新项目"开始您的 AI 开发之旅</p>
          </div>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectProject(project)}
              onKeyDown={(e) => handleCardKeyDown(e, project)}
              className="w-full text-left bg-white border border-gray-200 rounded-lg p-6 hover:border-[#2496ED] hover:shadow-md transition-[border-color,box-shadow] duration-200 group focus-visible:ring-2 focus-visible:ring-[#2496ED] focus-visible:ring-offset-2 cursor-pointer"
              aria-label={`选择项目 ${project.name}`}
            >
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-[#2496ED]">
                  {project.name}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteProject(project.name);
                  }}
                  className="px-3 py-1.5 text-xs text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors duration-200 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
                  aria-label={`删除项目 ${project.name}`}
                >
                  删除
                </button>
              </div>

              {project.description && (
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
              )}

              <div className="flex items-center gap-3 text-sm">
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getPhaseColor(project.current_phase)}`}>
                  {getPhaseLabel(project.current_phase)}
                </span>
                <span className="text-gray-500">v{project.prd_version}</span>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  更新于 {formatDate(project.updated_at)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}