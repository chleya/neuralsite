import { useState, useEffect, useRef } from 'react';
import { projectsApi, Project } from '../api/client';
import styles from './ProjectSelector.module.css';

interface ProjectSelectorProps {
  value?: string;
  onChange: (projectId: string | null) => void;
  placeholder?: string;
  showAll?: boolean;
  className?: string;
}

export default function ProjectSelector({
  value,
  onChange,
  placeholder = '选择项目',
  showAll = false,
  className,
}: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedProject = projects.find(p => p.project_id === value);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const res = await projectsApi.list({ limit: 100 });
        setProjects(res.projects);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredProjects = search
    ? projects.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.code?.toLowerCase().includes(search.toLowerCase())
      )
    : projects;

  const handleSelect = (projectId: string | null) => {
    onChange(projectId);
    setIsOpen(false);
    setSearch('');
  };

  return (
    <div className={`${styles.selector} ${className || ''}`} ref={dropdownRef}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => !loading && setIsOpen(!isOpen)}
        disabled={loading}
      >
        {loading ? (
          <span className={styles.placeholder}>加载中...</span>
        ) : selectedProject ? (
          <span className={styles.selected}>
            {selectedProject.name}
            {selectedProject.code && (
              <span className={styles.code}> ({selectedProject.code})</span>
            )}
          </span>
        ) : (
          <span className={styles.placeholder}>{placeholder}</span>
        )}
        <svg
          className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ''}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          <div className={styles.searchWrapper}>
            <svg
              className={styles.searchIcon}
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="搜索项目..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>

          <div className={styles.options}>
            {showAll && (
              <button
                type="button"
                className={`${styles.option} ${!value ? styles.optionSelected : ''}`}
                onClick={() => handleSelect(null)}
              >
                全部项目
              </button>
            )}

            {filteredProjects.length === 0 ? (
              <div className={styles.empty}>
                {search ? '未找到匹配的项目' : '暂无项目'}
              </div>
            ) : (
              filteredProjects.map((project) => (
                <button
                  key={project.project_id}
                  type="button"
                  className={`${styles.option} ${
                    project.project_id === value ? styles.optionSelected : ''
                  }`}
                  onClick={() => handleSelect(project.project_id)}
                >
                  <span className={styles.optionName}>{project.name}</span>
                  {project.code && (
                    <span className={styles.optionCode}>{project.code}</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
