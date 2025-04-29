import React, { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, ChartEvent, registerables } from 'chart.js';
import { Card } from 'react-bootstrap';
import { formatCurrency } from '../../utils/formatters';

// Registrar todos los componentes necesarios de Chart.js
Chart.register(...registerables);

interface PieChartProps {
  data: {
    id: number;
    name: string;
    total_amount: number;
  }[];
  title?: string;
  showLegend?: boolean;
}

const PieChart: React.FC<PieChartProps> = ({ 
  data, 
  title = 'Distribución por Categoría',
  showLegend = true 
}) => {
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<Chart | null>(null);

  // Colores para el gráfico
  const generateColors = (count: number) => {
    const baseColors = [
      'rgba(54, 162, 235, 0.8)',   // Azul
      'rgba(255, 99, 132, 0.8)',   // Rojo
      'rgba(255, 206, 86, 0.8)',   // Amarillo
      'rgba(75, 192, 192, 0.8)',   // Verde agua
      'rgba(153, 102, 255, 0.8)',  // Púrpura
      'rgba(255, 159, 64, 0.8)',   // Naranja
      'rgba(199, 199, 199, 0.8)',  // Gris
      'rgba(83, 102, 255, 0.8)',   // Azul violáceo
      'rgba(255, 99, 71, 0.8)',    // Tomate
      'rgba(144, 238, 144, 0.8)',  // Verde claro
    ];

    // Si hay más categorías que colores, repetimos los colores
    return Array(count).fill(0).map((_, i) => baseColors[i % baseColors.length]);
  };

  useEffect(() => {
    // Si no hay datos, no renderizamos el gráfico
    if (!data || data.length === 0 || !chartRef.current) {
      return;
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    // Destruir el gráfico anterior si existe
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    // Preparar datos para el gráfico
    const labels = data.map(item => item.name);
    const values = data.map(item => item.total_amount);
    const backgroundColor = generateColors(data.length);

    // Configuración del gráfico
    const config: ChartConfiguration = {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor,
          borderWidth: 1,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: showLegend,
            position: 'right',
          },
          tooltip: {
            callbacks: {
              label: function(tooltipItem) {
                const label = tooltipItem.label || '';
                const value = tooltipItem.raw as number;
                const percentage = (value / values.reduce((a, b) => a + b, 0) * 100).toFixed(1);
                return `${label}: ${formatCurrency(value)} (${percentage}%)`;
              }
            }
          }
        }
      }
    };

    // Crear el gráfico
    chartInstance.current = new Chart(ctx, config);

    // Cleanup al desmontar
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, showLegend]);

  return (
    <Card className="shadow-sm h-100">
      <Card.Body>
        <h5 className="card-title mb-3">{title}</h5>
        <div style={{ position: 'relative', height: '300px' }}>
          {data && data.length > 0 ? (
            <canvas ref={chartRef} />
          ) : (
            <div className="d-flex align-items-center justify-content-center h-100">
              <p className="text-muted">No hay datos disponibles</p>
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default PieChart; 