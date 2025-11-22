export function ProjectFormSimple() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">
            General Contractor AI
          </h1>
          <p className="text-gray-600 text-lg mt-2">
            Multi-agent construction project management system
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Type
              </label>
              <select className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                <option>Kitchen Remodel</option>
                <option>Bathroom Remodel</option>
                <option>New Construction</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Description
              </label>
              <textarea
                rows={6}
                placeholder="Describe your construction project..."
                className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg resize-none"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg"
            >
              Start Project
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
