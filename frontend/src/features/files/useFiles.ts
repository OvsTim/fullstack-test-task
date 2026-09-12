"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteFile, listFiles, updateFileTitle, uploadFile } from "@/features/files/api";
import { isFileInProgress, type FileItem } from "@/shared/types";

type ReloadOptions = {
  silent?: boolean;
};

function errorMessageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Произошла ошибка";
}

export function useFiles() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const reload = useCallback(async (options: ReloadOptions = {}) => {
    if (!options.silent) {
      setIsLoading(true);
    }
    setErrorMessage(null);

    try {
      setFiles(await listFiles());
    } catch (error) {
      setErrorMessage(errorMessageFrom(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const upload = useCallback(async (title: string, file: File) => {
    setErrorMessage(null);
    try {
      await uploadFile(title, file);
      await reload({ silent: true });
    } catch (error) {
      setErrorMessage(errorMessageFrom(error));
      throw error;
    }
  }, [reload]);

  const rename = useCallback(async (fileId: string, title: string) => {
    setErrorMessage(null);
    try {
      await updateFileTitle(fileId, title);
      await reload({ silent: true });
    } catch (error) {
      setErrorMessage(errorMessageFrom(error));
      throw error;
    }
  }, [reload]);

  const remove = useCallback(async (fileId: string) => {
    setErrorMessage(null);
    try {
      await deleteFile(fileId);
      await reload({ silent: true });
    } catch (error) {
      setErrorMessage(errorMessageFrom(error));
      throw error;
    }
  }, [reload]);

  const hasInProgress = files.some(isFileInProgress);

  return {
    files,
    isLoading,
    errorMessage,
    setErrorMessage,
    hasInProgress,
    reload,
    upload,
    rename,
    remove,
  };
}
