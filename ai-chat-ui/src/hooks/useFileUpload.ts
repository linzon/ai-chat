import { useState, useCallback } from 'react';
import { apiClient, type UploadResponse } from '../api/client';

export interface UploadedFile {
  id: string;
  file: File;
  url: string;
  name: string;
  type: string;
  previewUrl?: string;
}

export function useFileUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File): Promise<UploadedFile> => {
    setUploading(true);
    setError(null);
    
    try {
      // For image files, create a preview URL
      let previewUrl: string | undefined;
      if (file.type.startsWith('image/')) {
        previewUrl = URL.createObjectURL(file);
      }

      // Upload to the backend
      const response = await apiClient.uploadFile(file);

      const uploadedFile: UploadedFile = {
        id: Math.random().toString(36).substr(2, 9),
        file,
        url: `${apiClient.baseUrl}${response.url}`,  // 正确拼接基础URL和相对路径
        name: response.filename,
        type: response.content_type,
        previewUrl
      };

      setUploadedFiles(prev => [...prev, uploadedFile]);
      return uploadedFile;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '上传失败';
      setError(errorMessage);
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  const removeFile = useCallback((id: string) => {
    setUploadedFiles(prev => {
      const fileToRemove = prev.find(file => file.id === id);
      if (fileToRemove && fileToRemove.previewUrl) {
        URL.revokeObjectURL(fileToRemove.previewUrl);
      }
      return prev.filter(file => file.id !== id);
    });
  }, []);

  const clearFiles = useCallback(() => {
    // Revoke all preview URLs
    uploadedFiles.forEach(file => {
      if (file.previewUrl) {
        URL.revokeObjectURL(file.previewUrl);
      }
    });
    setUploadedFiles([]);
  }, [uploadedFiles]);

  return {
    uploadedFiles,
    uploading,
    error,
    uploadFile,
    removeFile,
    clearFiles
  };
}