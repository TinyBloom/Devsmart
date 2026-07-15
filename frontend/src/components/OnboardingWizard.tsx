import { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  X, 
  ChevronRight,
  Code2,
  Database,
  Cloud,
  FileText
} from 'lucide-react';
import type { OnboardingTemplate, OnboardingData, ProjectType } from '../types';
import { projectApi } from '../services/api';

interface OnboardingWizardProps {
  onComplete: (data: OnboardingData, projectType: ProjectType, projectName: string, sourcePath?: string) => void;
  onCancel: () => void;
  embedded?: boolean;
}

type Step = 'type' | 'basic' | 'tech' | 'database' | 'deploy' | 'confirm';

const stepConfig: Record<Step, { title: string; icon: typeof FileText }> = {
  type: { title: '项目类型', icon: FileText },
  basic: { title: '基本信息', icon: FileText },
  tech: { title: '技术选型', icon: Code2 },
  database: { title: '数据库选择', icon: Database },
  deploy: { title: '部署形式', icon: Cloud },
  confirm: { title: '确认信息', icon: Check },
};

export function OnboardingWizard({ onComplete, onCancel, embedded = false }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState<Step>('type');
  const [projectType, setProjectType] = useState<ProjectType>('greenfield');
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [sourcePath, setSourcePath] = useState('');
  const [template, setTemplate] = useState<OnboardingTemplate | null>(null);
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    requirement_description: '',
    backend_tech: '',
    frontend_tech: '',
    database: '',
    deployment: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading] = useState(false);

  useEffect(() => {
    projectApi.getOnboardingTemplate().then(setTemplate).catch(() => {});
  }, []);

  const steps: Step[] = ['type', 'basic', 'tech', 'database', 'deploy', 'confirm'];
  const currentIndex = steps.indexOf(currentStep);

  const validateStep = (step: Step): boolean => {
    const newErrors: Record<string, string> = {};
    
    switch (step) {
      case 'type':
        if (!projectType) newErrors.projectType = '请选择项目类型';
        break;
      case 'basic':
        if (!projectName.trim()) newErrors.projectName = '请输入项目名称';
        else if (!/^[a-zA-Z0-9_-]{3,64}$/.test(projectName)) {
          newErrors.projectName = '项目名称只能包含字母、数字、下划线、连字符，长度3-64';
        }
        if (projectType === 'incremental' && !sourcePath.trim()) {
          newErrors.sourcePath = '请输入现有项目路径';
        }
        break;
      case 'tech':
        if (!onboardingData.backend_tech) newErrors.backendTech = '请选择后端技术';
        if (!onboardingData.frontend_tech) newErrors.frontendTech = '请选择前端技术';
        break;
      case 'database':
        if (!onboardingData.database) newErrors.database = '请选择数据库';
        break;
      case 'deploy':
        if (!onboardingData.deployment) newErrors.deployment = '请选择部署形式';
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep) && currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  };

  const handleComplete = () => {
    if (validateStep('confirm')) {
      onComplete(onboardingData, projectType, projectName, sourcePath);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'type':
        return (
          <div className="space-y-6">
            <p className="text-gray-600">请选择项目类型</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setProjectType('greenfield')}
                className={`p-6 rounded-lg border-2 transition-[border-color,background-color] ${
                  projectType === 'greenfield'
                    ? 'border-[#2496ED] bg-[#E3F2FD]'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-4xl mb-4">🌱</div>
                <h3 className="text-lg font-semibold mb-2">全新项目</h3>
                <p className="text-sm text-gray-600">从无到有创建一个新项目，适合从零开始开发</p>
              </button>
              <button
                onClick={() => setProjectType('incremental')}
                className={`p-6 rounded-lg border-2 transition-[border-color,background-color] ${
                  projectType === 'incremental'
                    ? 'border-[#2496ED] bg-[#E3F2FD]'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-4xl mb-4">🔄</div>
                <h3 className="text-lg font-semibold mb-2">现有项目</h3>
                <p className="text-sm text-gray-600">在已有项目基础上添加新功能或修复 Bug</p>
              </button>
            </div>
          </div>
        );

      case 'basic':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">项目名称 *</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="例如: my-awesome-project"
                className={`w-full px-4 py-3 rounded-lg border ${
                  errors.projectName ? 'border-red-500' : 'border-gray-300'
                } focus:ring-2 focus:ring-[#2496ED] focus:border-transparent`}
              />
              {errors.projectName && (
                <p className="text-red-500 text-sm mt-1">{errors.projectName}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">项目描述</label>
              <textarea
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="简要描述您的项目..."
                rows={3}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-[#2496ED] focus:border-transparent"
              />
            </div>
            {projectType === 'incremental' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">项目路径 *</label>
                <input
                  type="text"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                  placeholder="例如: /home/user/projects/my-project"
                  className={`w-full px-4 py-3 rounded-lg border ${
                    errors.sourcePath ? 'border-red-500' : 'border-gray-300'
                  } focus:ring-2 focus:ring-[#2496ED] focus:border-transparent`}
                />
                {errors.sourcePath && (
                  <p className="text-red-500 text-sm mt-1">{errors.sourcePath}</p>
                )}
              </div>
            )}
          </div>
        );

      case 'tech':
        if (!template) return <p className="text-gray-500">加载中...</p>;
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">后端技术选型 *</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {template.sections.backend_tech.options?.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setOnboardingData({ ...onboardingData, backend_tech: opt.value })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      onboardingData.backend_tech === opt.value
                        ? 'border-[#2496ED] bg-[#E3F2FD]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium mb-1">{opt.label}</div>
                    <div className="text-sm text-gray-600">{opt.description}</div>
                  </button>
                ))}
              </div>
              {errors.backendTech && (
                <p className="text-red-500 text-sm mt-1">{errors.backendTech}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">前端技术选型 *</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {template.sections.frontend_tech.options?.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setOnboardingData({ ...onboardingData, frontend_tech: opt.value })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      onboardingData.frontend_tech === opt.value
                        ? 'border-[#2496ED] bg-[#E3F2FD]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium mb-1">{opt.label}</div>
                    <div className="text-sm text-gray-600">{opt.description}</div>
                  </button>
                ))}
              </div>
              {errors.frontendTech && (
                <p className="text-red-500 text-sm mt-1">{errors.frontendTech}</p>
              )}
            </div>
          </div>
        );

      case 'database':
        if (!template) return <p className="text-gray-500">加载中...</p>;
        return (
          <div className="space-y-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">数据库选择 *</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {template.sections.database.options?.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setOnboardingData({ ...onboardingData, database: opt.value })}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    onboardingData.database === opt.value
                      ? 'border-[#2496ED] bg-[#E3F2FD]'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium mb-1">{opt.label}</div>
                  <div className="text-sm text-gray-600">{opt.description}</div>
                </button>
              ))}
            </div>
            {errors.database && (
              <p className="text-red-500 text-sm mt-1">{errors.database}</p>
            )}
          </div>
        );

      case 'deploy':
        if (!template) return <p className="text-gray-500">加载中...</p>;
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">需求描述 *</label>
              <textarea
                value={onboardingData.requirement_description}
                onChange={(e) => setOnboardingData({ ...onboardingData, requirement_description: e.target.value })}
                placeholder="请详细描述您想要开发的功能、业务场景和期望目标..."
                rows={6}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-[#2496ED] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">部署形式 *</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {template.sections.deployment.options?.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setOnboardingData({ ...onboardingData, deployment: opt.value })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      onboardingData.deployment === opt.value
                        ? 'border-[#2496ED] bg-[#E3F2FD]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium mb-1">{opt.label}</div>
                    <div className="text-sm text-gray-600">{opt.description}</div>
                  </button>
                ))}
              </div>
              {errors.deployment && (
                <p className="text-red-500 text-sm mt-1">{errors.deployment}</p>
              )}
            </div>
          </div>
        );

      case 'confirm':
        const getTechLabel = (key: string, section: string) => {
          if (!template) return key;
          return template.sections[section]?.options?.find((o) => o.value === key)?.label || key;
        };

        return (
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">项目信息</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">项目类型</span>
                  <span className="font-medium">{projectType === 'greenfield' ? '全新项目' : '现有项目'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">项目名称</span>
                  <span className="font-medium">{projectName}</span>
                </div>
                {projectDescription && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">项目描述</span>
                    <span className="font-medium">{projectDescription}</span>
                  </div>
                )}
                {projectType === 'incremental' && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">项目路径</span>
                    <span className="font-medium">{sourcePath}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">技术选型</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">后端技术</span>
                  <span className="font-medium">{getTechLabel(onboardingData.backend_tech, 'backend_tech')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">前端技术</span>
                  <span className="font-medium">{getTechLabel(onboardingData.frontend_tech, 'frontend_tech')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">数据库</span>
                  <span className="font-medium">{getTechLabel(onboardingData.database, 'database')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">部署形式</span>
                  <span className="font-medium">{getTechLabel(onboardingData.deployment, 'deployment')}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold mb-4">需求描述</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{onboardingData.requirement_description}</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`${embedded ? '' : 'fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50'}`}>
      <div className={`bg-white rounded-lg shadow-lg ${embedded ? 'h-full' : 'w-full max-w-2xl max-h-[90vh]'} overflow-hidden flex flex-col`}>
        <div className="flex items-center justify-between p-6 border-b bg-gray-50">
          <div className="flex items-center gap-4">
            {steps.map((step, index) => {
              const Icon = stepConfig[step].icon;
              const isActive = step === currentStep;
              const isPast = index < currentIndex;
              return (
                <div key={step} className="flex items-center gap-2">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-[background-color] ${
                      isActive
                        ? 'bg-[#2496ED] text-white'
                        : isPast
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {isPast ? <Check size={18} /> : <Icon size={18} />}
                  </div>
                  {index < steps.length - 1 && (
                    <ChevronRight className="text-gray-400 mx-2" size={16} />
                  )}
                </div>
              );
            })}
          </div>
          {!embedded && (
            <button onClick={onCancel} className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
              <X size={20} className="text-gray-500" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <h2 className="text-xl font-bold mb-6 text-gray-900">{stepConfig[currentStep].title}</h2>
          {renderStepContent()}
        </div>

        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-[background-color] ${
              currentIndex === 0
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            <ArrowLeft size={18} />
            上一步
          </button>

          {currentStep === 'confirm' ? (
            <button
              onClick={handleComplete}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium bg-[#2496ED] text-white hover:bg-blue-700 transition-[background-color] disabled:opacity-50"
            >
              {loading ? '创建中...' : '确认创建'}
              <Check size={18} />
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium bg-[#2496ED] text-white hover:bg-blue-700 transition-[background-color]"
            >
              下一步
              <ArrowRight size={18} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}