import React, { useState, useEffect } from 'react';
import { Form, Row, Col, Button } from 'react-bootstrap';
import { Calendar3 } from 'react-bootstrap-icons';

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onDateChange: (startDate: string, endDate: string) => void;
  showPresets?: boolean;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onDateChange,
  showPresets = true
}) => {
  const [start, setStart] = useState(startDate);
  const [end, setEnd] = useState(endDate);

  // Actualizar estado local cuando cambian las props
  useEffect(() => {
    setStart(startDate);
    setEnd(endDate);
  }, [startDate, endDate]);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStart(e.target.value);
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEnd(e.target.value);
  };

  const handleApply = () => {
    onDateChange(start, end);
  };

  // Funciones para establecer rangos predefinidos
  const setCurrentMonth = () => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    setStart(formatDate(firstDay));
    setEnd(formatDate(lastDay));
    
    // Aplicar cambio inmediatamente
    onDateChange(formatDate(firstDay), formatDate(lastDay));
  };

  const setLastMonth = () => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth(), 0);
    
    setStart(formatDate(firstDay));
    setEnd(formatDate(lastDay));
    
    // Aplicar cambio inmediatamente
    onDateChange(formatDate(firstDay), formatDate(lastDay));
  };

  const setLastThreeMonths = () => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth() - 2, 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    setStart(formatDate(firstDay));
    setEnd(formatDate(lastDay));
    
    // Aplicar cambio inmediatamente
    onDateChange(formatDate(firstDay), formatDate(lastDay));
  };

  const setYear = () => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), 0, 1);
    const lastDay = new Date(now.getFullYear(), 11, 31);
    
    setStart(formatDate(firstDay));
    setEnd(formatDate(lastDay));
    
    // Aplicar cambio inmediatamente
    onDateChange(formatDate(firstDay), formatDate(lastDay));
  };

  // Función auxiliar para formatear fechas
  const formatDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="date-range-picker">
      <Row className="align-items-end g-2">
        <Col xs={12} sm={showPresets ? 6 : 5} md={showPresets ? 3 : 5} lg={showPresets ? 3 : 4}>
          <Form.Group>
            <Form.Label className="small">Fecha inicio</Form.Label>
            <Form.Control
              type="date"
              value={start}
              onChange={handleStartChange}
              max={end}
            />
          </Form.Group>
        </Col>
        
        <Col xs={12} sm={showPresets ? 6 : 5} md={showPresets ? 3 : 5} lg={showPresets ? 3 : 4}>
          <Form.Group>
            <Form.Label className="small">Fecha fin</Form.Label>
            <Form.Control
              type="date"
              value={end}
              onChange={handleEndChange}
              min={start}
            />
          </Form.Group>
        </Col>
        
        {showPresets && (
          <Col xs={12} sm={8} md={4} lg={4}>
            <div className="d-flex gap-1 mb-0 flex-wrap">
              <Button size="sm" variant="outline-secondary" onClick={setCurrentMonth}>
                Mes actual
              </Button>
              <Button size="sm" variant="outline-secondary" onClick={setLastMonth}>
                Mes anterior
              </Button>
              <Button size="sm" variant="outline-secondary" onClick={setLastThreeMonths}>
                Últimos 3 meses
              </Button>
              <Button size="sm" variant="outline-secondary" onClick={setYear}>
                Año actual
              </Button>
            </div>
          </Col>
        )}
        
        <Col xs={12} sm={showPresets ? 4 : 2} md={showPresets ? 2 : 2} lg={showPresets ? 2 : 4}>
          <div className="d-grid">
            <Button 
              variant="primary"
              onClick={handleApply}
              className="d-flex align-items-center justify-content-center gap-1"
            >
              <Calendar3 size={16} />
              <span>Aplicar</span>
            </Button>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default DateRangePicker; 