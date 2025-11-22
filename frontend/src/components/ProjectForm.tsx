import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useProjectStore } from '../store/projectStore';
import toast from 'react-hot-toast';
import { Building2, Hammer, Info } from 'lucide-react';

const PROJECT_TYPES = [
  { value: 'kitchen_remodel', label: 'Kitchen Remodel', template: true },
  { value: 'bathroom_remodel', label: 'Bathroom Remodel', template: true },
  { value: 'new_construction', label: 'New Construction', template: true },
  { value: 'addition', label: 'Addition', template: true },
  { value: 'shed_construction', label: 'Shed Construction', template: true },
  { value: 'custom', label: 'Custom Project', template: false },
];

export function ProjectForm() {
  const navigate = useNavigate();
  const { setLoading, setError } = useProjectStore();

  const [formData, setFormData] = useState({
    projectType: 'kitchen_remodel',
    description: '',
    useDynamicPlanning: false,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPlanningInfo, setShowPlanningInfo] = useState(false);

  const selectedProjectType = PROJECT_TYPES.find((pt) => pt.value === formData.projectType);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.description.trim()) {
      toast.error('Please provide a project description');
      return;
    }

    setIsSubmitting(true);
    setLoading(true);
    setError(null);

    try {
      const usingDynamicPlanning = formData.useDynamicPlanning || formData.projectType === 'custom';

      // Step 1: Start the project (creates tasks)
      await apiClient.startProject({
        description: formData.description,
        project_type: formData.projectType === 'custom' ? 'custom_project' : formData.projectType,
        use_dynamic_planning: usingDynamicPlanning,
      });

      toast.success('Project created! Starting autonomous execution...');

      // Step 2: Clean up form state BEFORE navigation
      setIsSubmitting(false);
      setLoading(false);

      // Step 3: Navigate to dashboard
      navigate('/dashboard');

      // Step 4: Give a moment for dashboard to mount, then start execution
      // This ensures the dashboard is ready to display progress
      setTimeout(async () => {
        try {
          await apiClient.executeAll();
        } catch (error) {
          console.error('Execution error:', error);
          toast.error('Execution failed - check dashboard for details');
        }
      }, 500);
    } catch (error: any) {
      console.error('Error starting project:', error);
      const errorMessage = error.message || 'Failed to start project';
      setError(errorMessage);
      toast.error(errorMessage);
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Building2 className="w-12 h-12 text-blue-600 dark:text-blue-400 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              General Contractor AI
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Multi-agent construction project management system
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 border border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Type */}
            <div>
              <label
                htmlFor="projectType"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Project Type
              </label>
              <select
                id="projectType"
                value={formData.projectType}
                onChange={(e) =>
                  setFormData({ ...formData, projectType: e.target.value })
                }
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 dark:text-white"
              >
                {PROJECT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label} {type.template ? '(Template)' : '(Custom)'}
                  </option>
                ))}
              </select>
              {selectedProjectType && !selectedProjectType.template && (
                <p className="mt-2 text-sm text-blue-600 dark:text-blue-400">
                  Custom projects use AI-powered dynamic planning
                </p>
              )}
            </div>

            {/* Description */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Project Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={6}
                placeholder="Describe your construction project in detail... (e.g., 'Build a 10x12 shed with electricity, windows, and a concrete foundation')"
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            {/* Dynamic Planning Toggle */}
            {selectedProjectType?.template && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="useDynamicPlanning"
                    checked={formData.useDynamicPlanning}
                    onChange={(e) =>
                      setFormData({ ...formData, useDynamicPlanning: e.target.checked })
                    }
                    className="w-5 h-5 mt-0.5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <label
                        htmlFor="useDynamicPlanning"
                        className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
                      >
                        Generate custom AI plan (instead of using standard template)
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowPlanningInfo(!showPlanningInfo)}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition"
                        aria-label="More information about dynamic planning"
                      >
                        <Info className="w-4 h-4" />
                      </button>
                    </div>
                    {showPlanningInfo && (
                      <div className="mt-3 p-3 bg-white dark:bg-gray-800 rounded-md border border-blue-200 dark:border-blue-700 text-sm text-gray-600 dark:text-gray-400 space-y-2">
                        <p className="font-semibold text-gray-700 dark:text-gray-300">
                          What is Dynamic Planning?
                        </p>
                        <p>
                          AI analyzes your project description and generates a fully customized task breakdown tailored to your specific requirements.
                        </p>
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          <div>
                            <p className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
                              Standard Template
                            </p>
                            <ul className="text-xs space-y-1">
                              <li>✓ Predefined tasks</li>
                              <li>✓ Fast & predictable</li>
                              <li>✓ Best for common projects</li>
                            </ul>
                          </div>
                          <div>
                            <p className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
                              Dynamic Planning
                            </p>
                            <ul className="text-xs space-y-1">
                              <li>✓ Custom AI-generated tasks</li>
                              <li>✓ Adapts to your needs</li>
                              <li>✓ Best for unique requirements</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-4 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>
                    {formData.useDynamicPlanning || formData.projectType === 'custom'
                      ? 'Generating AI Project Plan...'
                      : 'Starting Project...'}
                  </span>
                </>
              ) : (
                <>
                  <Hammer className="w-5 h-5" />
                  <span>Start Project</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Info Card */}
        <div className="mt-6 bg-white/50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">How it works:</h3>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <li>• <strong>Choose planning method:</strong> Use predefined templates for common projects, or enable dynamic planning for AI-customized task breakdowns</li>
            <li>• <strong>AI coordination:</strong> Multiple specialized agents collaborate to manage your project</li>
            <li>• <strong>Real-time tracking:</strong> Watch agents work together on the dashboard</li>
            <li>• <strong>Complete management:</strong> Track materials, permits, and construction progress</li>
          </ul>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Or click here to go to dashboard manually →
          </button>
        </div>
      </div>
    </div>
  );
}
