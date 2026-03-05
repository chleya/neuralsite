import { useEffect, useCallback } from 'react';
import { useAppStore } from '../stores/appStore';
import { projectsApi, Project } from '../api/client';

interface UseProjectReturn {
  currentProjectId: string | null;
  currentProjectName: string | null;
  isLoading: boolean;
  setCurrentProject: (projectId: string | null, projectName?: string | null) => void;
  fetchProjectName: (projectId: string) => Promise<string | null>;
}

export function useProject(): UseProjectReturn {
  const {
    currentProjectId,
    currentProjectName,
    setCurrentProject: setProject,
  } = useAppStore();

  const [isLoading, setIsLoading] = React.useState(false);

  const setCurrentProject = useCallback((projectId: string | null, projectName?: string | null) => {
    if (projectId && !projectName) {
      // Fetch project name if not provided
      setIsLoading(true);
      projectsApi.get(projectId)
        .then((project) => {
          setProject(projectId, project.name);
        })
        .catch(console.error)
        .finally(() => setIsLoading(false));
    } else {
      setProject(projectId, projectName ?? null);
    }
  }, [setProject]);

  const fetchProjectName = useCallback(async (projectId: string): Promise<string | null> => {
    try {
      const project = await projectsApi.get(projectId);
      return project.name;
    } catch (error) {
      console.error('Failed to fetch project:', error);
      return null;
    }
  }, []);

  return {
    currentProjectId,
    currentProjectName,
    isLoading,
    setCurrentProject,
    fetchProjectName,
  };
}

import React from 'react';
export default useProject;
