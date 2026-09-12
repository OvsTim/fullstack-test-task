"use client";

import { Button, Modal } from "react-bootstrap";
import type { FileItem } from "@/shared/types";

type DeleteConfirmModalProps = {
  file: FileItem | null;
  isSubmitting: boolean;
  onHide: () => void;
  onConfirm: (fileId: string) => Promise<void>;
};

export function DeleteConfirmModal({
  file,
  isSubmitting,
  onHide,
  onConfirm,
}: DeleteConfirmModalProps) {
  return (
    <Modal show={file !== null} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Удалить файл?</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {file ? (
          <p className="mb-0">
            Файл «{file.title}» будет удалён вместе с связанными алертами.
          </p>
        ) : null}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={onHide} disabled={isSubmitting}>
          Отмена
        </Button>
        <Button
          variant="danger"
          disabled={isSubmitting || !file}
          onClick={() => {
            if (file) {
              void onConfirm(file.id);
            }
          }}
        >
          {isSubmitting ? "Удаление..." : "Удалить"}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
