/**
 * ProjectForm Component
 * 项目创建表单组件
 */

import { useState } from 'react';

interface ProjectFormProps {
  onSubmit: (name: string, description?: string) => void;
  onCancel: () => void;
}

export function ProjectForm({ onSubmit, onCancel }: ProjectFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nameError, setNameError] = useState('');

  const validateName = (value: string): boolean => {
    // 根据 PRD Section 5.0.4 规则校验
    if (value.length < 3) {
      setNameError('项目名称至少 3 个字符');
      return false;
    }
    if (value.length > 64) {
      setNameError('项目名称最多 64 个字符');
      return false;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
      setNameError('只能包含字母、数字、下划线、连字符');
      return false;
    }
    setNameError('');
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateName(name)) {
      onSubmit(name, description || undefined);
    }
  };

  return (
    <div className="project-form-overlay">
      <div className="project-form">
        <h2>新建项目</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">项目名称 *</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                validateName(e.target.value);
              }}
              placeholder="my-todo-app"
              className={nameError ? 'input-error' : ''}
            />
            {nameError && <p className="error-message">{nameError}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="description">项目描述</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="一个任务管理应用"
              rows={3}
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={onCancel} className="cancel-btn">
              取消
            </button>
            <button type="submit" className="submit-btn" disabled={!name || !!nameError}>
              创建项目
            </button>
          </div>
        </form>
      </div>

      <style>{`
        .project-form-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .project-form {
          background: white;
          padding: 30px;
          border-radius: 16px;
          width: 400px;
          max-width: 90%;
        }

        .project-form h2 {
          margin-bottom: 20px;
          font-size: 20px;
          color: #333;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-size: 14px;
          color: #666;
        }

        .form-group input,
        .form-group textarea {
          width: 100%;
          padding: 10px 15px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
        }

        .form-group input.input-error {
          border-color: #ff4444;
        }

        .error-message {
          color: #ff4444;
          font-size: 12px;
          margin-top: 5px;
        }

        .form-actions {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
        }

        .cancel-btn {
          padding: 10px 20px;
          background: #f0f0f0;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }

        .submit-btn {
          padding: 10px 20px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }

        .submit-btn:hover {
          background: #45a049;
        }

        .submit-btn:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}