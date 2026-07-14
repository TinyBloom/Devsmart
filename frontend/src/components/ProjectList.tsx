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
  return (
    <div className="project-list">
      {/* 搜索框 */}
      <div className="search-bar">
        <input
          type="text"
          placeholder="搜索项目..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="search-input"
        />
      </div>

      {/* 项目列表 */}
      <div className="projects-grid">
        {projects.length === 0 ? (
          <div className="no-projects">
            <p>暂无项目，点击"新建项目"开始</p>
          </div>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              className="project-card"
              onClick={() => onSelectProject(project)}
            >
              <div className="project-header">
                <h3 className="project-name">{project.name}</h3>
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteProject(project.name);
                  }}
                >
                  删除
                </button>
              </div>

              <div className="project-info">
                <div className="info-item">
                  <label>当前阶段</label>
                  <span className={`phase-badge ${project.current_phase}`}>
                    {project.current_phase}
                  </span>
                </div>

                <div className="info-item">
                  <label>PRD 版本</label>
                  <span>v{project.prd_version}</span>
                </div>

                <div className="info-item">
                  <label>最后修改</label>
                  <span>{new Date(project.updated_at).toLocaleString()}</span>
                </div>
              </div>

              {project.description && (
                <p className="project-description">{project.description}</p>
              )}
            </div>
          ))
        )}
      </div>

      <style>{`
        .project-list {
          padding: 20px;
        }

        .search-bar {
          margin-bottom: 20px;
        }

        .search-input {
          width: 100%;
          padding: 10px 15px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
        }

        .projects-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .project-card {
          border: 1px solid #ddd;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
        }

        .project-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .project-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .project-name {
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }

        .delete-btn {
          padding: 5px 10px;
          background: #ff4444;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
        }

        .delete-btn:hover {
          background: #cc0000;
        }

        .project-info {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 15px;
        }

        .info-item {
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .info-item label {
          font-size: 12px;
          color: #888;
        }

        .info-item span {
          font-size: 14px;
          color: #333;
        }

        .phase-badge {
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 12px;
          background: #e0e0e0;
        }

        .phase-badge.prd {
          background: #4CAF50;
          color: white;
        }

        .phase-badge.tech {
          background: #2196F3;
          color: white;
        }

        .project-description {
          font-size: 13px;
          color: #666;
          margin-top: 10px;
        }

        .no-projects {
          text-align: center;
          padding: 40px;
          color: #888;
        }
      `}</style>
    </div>
  );
}