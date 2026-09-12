"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button, Form, Modal } from "react-bootstrap";
import type { FileItem } from "@/shared/types";

type RenameModalProps = {
  file: FileItem | null;
  isSubmitting: boolean;
  onHide: () => void;
  onSubmit: (fileId: string, title: string) => Promise<void>;
};

export function RenameModal({ file, isSubmitting, onHide, onSubmit }: RenameModalProps) {
  const [title, setTitle] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(file?.title ?? "");
    setLocalError(null);
  }, [file]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      return;
    }

    if (!title.trim()) {
      setLocalError("Укажите название");
      return;
    }

    setLocalError(null);
    await onSubmit(file.id, title.trim());
  }

  return (
    <Modal show={file !== null} onHide={onHide} centered>
      <Form onSubmit={(event) => void handleSubmit(event)}>
        <Modal.Header closeButton>
          <Modal.Title>Переименовать файл</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {localError ? <p className="text-danger small">{localError}</p> : null}
          <Form.Group>
            <Form.Label>Название</Form.Label>
            <Form.Control
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>
            Отмена
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? "Сохранение..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
