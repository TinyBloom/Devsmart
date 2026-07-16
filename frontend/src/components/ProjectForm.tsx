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

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (validateName(name)) {
      onSubmit(name, description || undefined);
    }
  };

  return (
    <div className="project-form-overlay" role="dialog" aria-modal="true" aria-labelledby="project-form-title">
      <div className="project-form">
        <h2 id="project-form-title">新建项目</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="project-name">项目名称 *</label>
            <input
              type="text"
              id="project-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              onBlur={() => name && validateName(name)}
              placeholder="my-todo-app"
              className={nameError ? 'input-error' : ''}
              aria-invalid={Boolean(nameError)}
              aria-describedby={nameError ? 'project-name-error' : undefined}
            />
            {nameError && <p id="project-name-error" className="error-message">{nameError}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="project-description">项目描述</label>
            <textarea
              id="project-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
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
    </div>
  );
}
