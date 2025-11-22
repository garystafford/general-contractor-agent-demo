import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';

export function DashboardTest() {
  const navigate = useNavigate();
  const { project, projectStatus } = useProjectStore();

  useEffect(() => {
    console.log('Dashboard - project:', project);
    console.log('Dashboard - projectStatus:', projectStatus);
  }, [project, projectStatus]);

  return (
    <div style={{ padding: '40px', background: 'lightgreen', minHeight: '100vh' }}>
      <h1 style={{ color: 'black', fontSize: '32px' }}>Dashboard Loaded!</h1>

      {project ? (
        <div style={{ marginTop: '20px', color: 'black' }}>
          <h2>Project Details:</h2>
          <p><strong>Description:</strong> {project.description}</p>
          <p><strong>Type:</strong> {project.type}</p>
          <p><strong>Status:</strong> {project.status}</p>

          {projectStatus && (
            <div style={{ marginTop: '20px' }}>
              <h2>Task Summary:</h2>
              <p>Total Tasks: {projectStatus.task_status.total_tasks}</p>
              <p>Completed: {projectStatus.task_status.completed}</p>
              <p>Pending: {projectStatus.task_status.pending}</p>
            </div>
          )}
        </div>
      ) : (
        <p style={{ color: 'black' }}>No project data found. Check console for details.</p>
      )}

      <button
        onClick={() => navigate('/')}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          background: 'blue',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        Back to Form
      </button>
    </div>
  );
}
