/**
 * Formatea un valor numérico como moneda en formato local
 * @param value Valor numérico a formatear
 * @param locale Configuración regional (por defecto es-AR)
 * @returns String formateado como moneda
 */
export const formatCurrency = (value: number, locale = 'es-AR'): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

/**
 * Formatea una fecha ISO en formato local
 * @param dateString Fecha en formato ISO o string compatible
 * @param locale Configuración regional (por defecto es-AR)
 * @returns String con la fecha formateada
 */
export const formatDate = (dateString: string, locale = 'es-AR'): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString(locale);
};

/**
 * Formatea un porcentaje
 * @param value Valor a formatear (0.1 = 10%)
 * @param decimals Número de decimales a mostrar
 * @returns String formateado como porcentaje
 */
export const formatPercent = (value: number, decimals = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
}; 