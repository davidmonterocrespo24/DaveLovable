import { useParams } from 'react-router-dom';
import { useProject } from '@/hooks/useProjects';
import { useFiles } from '@/hooks/useFiles';

const EditorDebug = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const numProjectId = Number(projectId);

  const { data: project, isLoading: projectLoading, error: projectError } = useProject(numProjectId);
  const { data: files, isLoading: filesLoading, error: filesError } = useFiles(numProjectId);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Editor Debug Info</h1>

      <div className="space-y-4">
        <div>
          <h2 className="font-bold">Project ID:</h2>
          <p>String: {projectId}</p>
          <p>Number: {numProjectId}</p>
          <p>Is NaN: {isNaN(numProjectId) ? 'YES' : 'NO'}</p>
        </div>

        <div>
          <h2 className="font-bold">Project Data:</h2>
          <p>Loading: {projectLoading ? 'YES' : 'NO'}</p>
          <p>Error: {projectError ? JSON.stringify(projectError) : 'None'}</p>
          <pre>{JSON.stringify(project, null, 2)}</pre>
        </div>

        <div>
          <h2 className="font-bold">Files Data:</h2>
          <p>Loading: {filesLoading ? 'YES' : 'NO'}</p>
          <p>Error: {filesError ? JSON.stringify(filesError) : 'None'}</p>
          <p>Files count: {files?.length || 0}</p>
          <pre>{JSON.stringify(files, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
};

export default EditorDebug;
