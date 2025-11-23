import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useProjectStore, type ErrorDetail } from '../store/projectStore';
import toast from 'react-hot-toast';
import { Building2, Hammer, Info } from 'lucide-react';
import ErrorModal from './ErrorModal';

const PROJECT_TYPES = [
  { value: 'kitchen_remodel', label: 'Kitchen Remodel', template: true },
  { value: 'bathroom_remodel', label: 'Bathroom Remodel', template: true },
  { value: 'new_construction', label: 'New Construction', template: true },
  { value: 'addition', label: 'Addition', template: true },
  { value: 'shed_construction', label: 'Shed Construction', template: true },
  { value: 'custom', label: 'Custom Project', template: false },
];

function validateProjectDescription(projectType: string, description: string): ErrorDetail | null {
  const missingFields: string[] = [];
  const suggestions: string[] = [];

  if (!description.trim()) {
    return null; // Will be caught by existing validation
  }

  const lowerDesc = description.toLowerCase();

  switch (projectType) {
    case 'kitchen_remodel':
      // Check for dimensions
      if (!description.match(/\d+\s*[xX×]\s*\d+/) && !lowerDesc.includes('feet') && !lowerDesc.includes('square')) {
        missingFields.push('Kitchen dimensions (e.g., "12 feet by 15 feet" or "12x15")');
        suggestions.push('Add the length and width of your kitchen space');
      }

      // Check for style preference
      const styles = ['modern', 'traditional', 'transitional', 'farmhouse', 'contemporary', 'rustic'];
      if (!styles.some(style => lowerDesc.includes(style))) {
        missingFields.push('Kitchen style preference (modern, traditional, transitional, or farmhouse)');
        suggestions.push('Specify your preferred kitchen style');
      }
      break;

    case 'bathroom_remodel':
      // Check for dimensions
      if (!description.match(/\d+\s*[xX×]\s*\d+/) && !lowerDesc.includes('feet') && !lowerDesc.includes('square')) {
        missingFields.push('Bathroom dimensions (e.g., "8x10 feet")');
        suggestions.push('Add the dimensions of your bathroom');
      }

      // Check for fixtures mentioned
      const fixtures = ['toilet', 'sink', 'shower', 'tub', 'bathtub', 'vanity'];
      if (!fixtures.some(fixture => lowerDesc.includes(fixture))) {
        missingFields.push('Fixture requirements (toilet, sink, shower, tub, etc.)');
        suggestions.push('List which fixtures you want to install or replace');
      }
      break;

    case 'addition':
      // Check for square footage or dimensions
      if (!lowerDesc.includes('square') && !lowerDesc.includes('sq') && !description.match(/\d+\s*[xX×]\s*\d+/)) {
        missingFields.push('Size of addition (square footage or dimensions)');
        suggestions.push('Specify how large the addition should be');
      }

      // Check for room type
      if (!lowerDesc.includes('bedroom') && !lowerDesc.includes('room') &&
          !lowerDesc.includes('office') && !lowerDesc.includes('living') &&
          !lowerDesc.includes('family')) {
        missingFields.push('Type of room being added (bedroom, office, family room, etc.)');
        suggestions.push('Describe what type of space you\'re adding');
      }
      break;

    case 'shed_construction':
      // Check for dimensions
      if (!description.match(/\d+\s*[xX×]\s*\d+/)) {
        missingFields.push('Shed dimensions (e.g., "10x12 feet")');
        suggestions.push('Specify the length and width of the shed');
      }
      break;

    case 'new_construction':
      // Check for square footage
      if (!lowerDesc.includes('square') && !lowerDesc.includes('sq ft') && !lowerDesc.includes('sqft')) {
        missingFields.push('Total square footage of the building');
        suggestions.push('Provide the total size of the construction project');
      }

      // Check for number of floors/stories
      if (!lowerDesc.includes('story') && !lowerDesc.includes('stories') &&
          !lowerDesc.includes('floor') && !lowerDesc.includes('level')) {
        missingFields.push('Number of floors/stories');
        suggestions.push('Specify how many floors the building will have');
      }
      break;
  }

  if (missingFields.length > 0) {
    return {
      type: 'missing_info',
      title: 'Missing Required Information',
      message: `Your ${PROJECT_TYPES.find(pt => pt.value === projectType)?.label || 'project'} description needs additional details to proceed.`,
      missingFields,
      suggestions,
    };
  }

  return null;
}

export function ProjectForm() {
  const navigate = useNavigate();
  const { setLoading, setError, showErrorModal, closeErrorModal, errorModal, isErrorModalOpen } = useProjectStore();

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

    // Validate project description for required information (skip for custom projects)
    if (formData.projectType !== 'custom') {
      const validationError = validateProjectDescription(formData.projectType, formData.description);
      if (validationError) {
        showErrorModal(validationError);
        return;
      }
    }

    setIsSubmitting(true);
    setLoading(true);
    setError(null);

    try {
      const usingDynamicPlanning = formData.useDynamicPlanning || formData.projectType === 'custom';

      console.log('Starting project...', { description: formData.description, usingDynamicPlanning });

      // Step 1: Start the project (creates tasks)
      const result = await apiClient.startProject({
        description: formData.description,
        project_type: formData.projectType === 'custom' ? 'custom_project' : formData.projectType,
        use_dynamic_planning: usingDynamicPlanning,
      });

      console.log('Project started successfully:', result);

      toast.success('Project created! Starting autonomous execution...');

      // Step 2: Navigate immediately (don't wait for state updates)
      console.log('Navigating to dashboard...');
      navigate('/dashboard');

      // Step 3: Start execution in background
      setTimeout(async () => {
        try {
          console.log('Starting autonomous execution...');
          await apiClient.executeAll();
          console.log('Execution completed');
        } catch (error) {
          console.error('Execution error:', error);
          toast.error('Execution failed - check dashboard for details');
        }
      }, 1000);
    } catch (error: any) {
      console.error('Error starting project:', error);
      const errorMessage = error.message || 'Failed to start project';

      // Check if this is a structured validation error from backend
      if (error.detail && typeof error.detail === 'object' && error.detail.missing_fields) {
        showErrorModal({
          type: 'missing_info',
          title: 'Missing Required Information',
          message: error.detail.message || 'The project description is missing required information.',
          missingFields: error.detail.missing_fields,
          suggestions: error.detail.suggestions || [],
        });
      } else {
        setError(errorMessage);
        toast.error(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  const handleEditDescription = () => {
    // Focus on the textarea when user wants to edit
    const textarea = document.getElementById('description') as HTMLTextAreaElement;
    if (textarea) {
      textarea.focus();
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
          <div className="mt-3 flex gap-4 text-sm">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Go to dashboard →
            </button>
            <button
              onClick={() => navigate('/health')}
              className="text-green-600 dark:text-green-400 hover:underline"
            >
              System health status →
            </button>
          </div>
        </div>
      </div>

      {/* Error Modal */}
      <ErrorModal
        isOpen={isErrorModalOpen}
        onClose={closeErrorModal}
        error={errorModal}
        onEdit={handleEditDescription}
      />
    </div>
  );
}
