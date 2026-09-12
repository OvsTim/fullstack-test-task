"use client";

import { useCallback, useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Col, Container, Row } from "react-bootstrap";
import { useAlerts } from "@/features/alerts/useAlerts";
import { AlertsTable } from "@/features/alerts/ui/AlertsTable";
import { useFiles } from "@/features/files/useFiles";
import { DeleteConfirmModal } from "@/features/files/ui/DeleteConfirmModal";
import { FilesTable } from "@/features/files/ui/FilesTable";
import { RenameModal } from "@/features/files/ui/RenameModal";
import { UploadModal } from "@/features/files/ui/UploadModal";
import type { FileItem } from "@/shared/types";

const POLL_INTERVAL_MS = 2500;

export function Dashboard() {
  const files = useFiles();
  const alerts = useAlerts();

  const [showUpload, setShowUpload] = useState(false);
  const [fileToRename, setFileToRename] = useState<FileItem | null>(null);
  const [fileToDelete, setFileToDelete] = useState<FileItem | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reloadAll = useCallback(
    async (silent = false) => {
      await Promise.all([
        files.reload({ silent }),
        alerts.reload({ silent }),
      ]);
    },
    [files.reload, alerts.reload],
  );

  useEffect(() => {
    if (!files.hasInProgress) {
      return;
    }

    const timer = window.setInterval(() => {
      void reloadAll(true);
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [files.hasInProgress, reloadAll]);

  const errorMessage = files.errorMessage ?? alerts.errorMessage;

  async function handleUpload(title: string, file: File) {
    setIsSubmitting(true);
    try {
      await files.upload(title, file);
      await alerts.reload({ silent: true });
      setShowUpload(false);
    } catch {
      // error is already on files.errorMessage
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRename(fileId: string, title: string) {
    setIsSubmitting(true);
    try {
      await files.rename(fileId, title);
      setFileToRename(null);
    } catch {
      // error is already on files.errorMessage
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(fileId: string) {
    setIsSubmitting(true);
    try {
      await files.remove(fileId);
      await alerts.reload({ silent: true });
      setFileToDelete(null);
    } catch {
      // error is already on files.errorMessage
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <Card className="shadow-sm border-0 mb-4">
            <Card.Body className="p-4">
              <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                  <h1 className="h3 mb-2">Управление файлами</h1>
                  <p className="text-secondary mb-0">
                    Загрузка файлов, просмотр статусов обработки и ленты алертов.
                  </p>
                </div>
                <div className="d-flex gap-2">
                  <Button variant="outline-secondary" onClick={() => void reloadAll()}>
                    Обновить
                  </Button>
                  <Button variant="primary" onClick={() => setShowUpload(true)}>
                    Добавить файл
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>

          {errorMessage ? (
            <Alert variant="danger" className="shadow-sm">
              {errorMessage}
            </Alert>
          ) : null}

          <Card className="shadow-sm border-0 mb-4">
            <Card.Header className="bg-white border-0 pt-4 px-4">
              <div className="d-flex justify-content-between align-items-center">
                <h2 className="h5 mb-0">Файлы</h2>
                <Badge bg="secondary">{files.files.length}</Badge>
              </div>
            </Card.Header>
            <Card.Body className="px-4 pb-4">
              <FilesTable
                files={files.files}
                isLoading={files.isLoading}
                onRename={setFileToRename}
                onDelete={setFileToDelete}
              />
            </Card.Body>
          </Card>

          <Card className="shadow-sm border-0">
            <Card.Header className="bg-white border-0 pt-4 px-4">
              <div className="d-flex justify-content-between align-items-center">
                <h2 className="h5 mb-0">Алерты</h2>
                <Badge bg="secondary">{alerts.alerts.length}</Badge>
              </div>
            </Card.Header>
            <Card.Body className="px-4 pb-4">
              <AlertsTable alerts={alerts.alerts} isLoading={alerts.isLoading} />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <UploadModal
        show={showUpload}
        isSubmitting={isSubmitting}
        onHide={() => setShowUpload(false)}
        onSubmit={handleUpload}
      />
      <RenameModal
        file={fileToRename}
        isSubmitting={isSubmitting}
        onHide={() => setFileToRename(null)}
        onSubmit={handleRename}
      />
      <DeleteConfirmModal
        file={fileToDelete}
        isSubmitting={isSubmitting}
        onHide={() => setFileToDelete(null)}
        onConfirm={handleDelete}
      />
    </Container>
  );
}
