"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button, Form, Modal } from "react-bootstrap";

type UploadModalProps = {
  show: boolean;
  isSubmitting: boolean;
  onHide: () => void;
  onSubmit: (title: string, file: File) => Promise<void>;
};

export function UploadModal({ show, isSubmitting, onHide, onSubmit }: UploadModalProps) {
  const [title, setTitle] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!show) {
      setTitle("");
      setSelectedFile(null);
      setLocalError(null);
    }
  }, [show]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!title.trim() || !selectedFile) {
      setLocalError("Укажите название и выберите файл");
      return;
    }

    setLocalError(null);
    await onSubmit(title.trim(), selectedFile);
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Form onSubmit={(event) => void handleSubmit(event)}>
        <Modal.Header closeButton>
          <Modal.Title>Добавить файл</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {localError ? <p className="text-danger small">{localError}</p> : null}
          <Form.Group className="mb-3">
            <Form.Label>Название</Form.Label>
            <Form.Control
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Например, Договор с подрядчиком"
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Файл</Form.Label>
            <Form.Control
              type="file"
              onChange={(event) =>
                setSelectedFile((event.target as HTMLInputElement).files?.[0] ?? null)
              }
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={onHide}>
            Отмена
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? "Загрузка..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
