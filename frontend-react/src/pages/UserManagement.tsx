import { useState } from 'react';
import {
  Container,
  Card,
  Button
} from 'react-bootstrap';
import { PeopleFill } from 'react-bootstrap-icons';

const UserManagement = () => {
  return (
    <Container fluid>
      <h1 className="mb-4">Gestión de Usuarios</h1>
      <Card className="shadow-sm">
        <Card.Body className="p-4">
          <p>Esta página está en desarrollo. Aquí se podrán administrar los usuarios del sistema.</p>
          <Button variant="primary" className="mt-3">
            <PeopleFill className="me-2" /> Nuevo Usuario
          </Button>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default UserManagement; 