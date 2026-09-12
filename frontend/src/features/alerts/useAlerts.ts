"use client";

import { useCallback, useEffect, useState } from "react";
import { listAlerts } from "@/features/alerts/api";
import type { AlertItem } from "@/shared/types";

type ReloadOptions = {
  silent?: boolean;
};

function errorMessageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Произошла ошибка";
}

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const reload = useCallback(async (options: ReloadOptions = {}) => {
    if (!options.silent) {
      setIsLoading(true);
    }
    setErrorMessage(null);

    try {
      setAlerts(await listAlerts());
    } catch (error) {
      setErrorMessage(errorMessageFrom(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    alerts,
    isLoading,
    errorMessage,
    reload,
  };
}
