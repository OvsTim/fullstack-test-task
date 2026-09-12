import { apiGet, apiSend, apiUrl } from "@/shared/api/client";
import type { FileItem } from "@/shared/types";

export function listFiles(): Promise<FileItem[]> {
  return apiGet<FileItem[]>("/files");
}

export function uploadFile(title: string, file: File): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  return apiSend<FileItem>("/files", {
    method: "POST",
    body: formData,
    fallbackError: "Не удалось загрузить файл",
  });
}

export function updateFileTitle(fileId: string, title: string): Promise<FileItem> {
  return apiSend<FileItem>(`/files/${fileId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
    fallbackError: "Не удалось переименовать файл",
  });
}

export function deleteFile(fileId: string): Promise<void> {
  return apiSend(`/files/${fileId}`, {
    method: "DELETE",
    fallbackError: "Не удалось удалить файл",
  });
}

export function downloadUrl(fileId: string): string {
  return apiUrl(`/files/${fileId}/download`);
}
