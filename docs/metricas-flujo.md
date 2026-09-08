# Catálogo de Métricas de Flujo de Desarrollo

## 1. Lead Time de Resolución de Issues ($LT_{issue}$)

- **Definición:** Tiempo total transcurrido desde que un issue es creado hasta que pasa a estado `closed`.
- **Unidad:** Horas y Días (punto flotante).
- **Fórmula:**
  $$LT_{issue} = \frac{\text{closed\_at} - \text{created\_at}}{3600 \text{ segundos}}$$
- **Filtros / Reglas de negocio:**
  - Aplica únicamente a issues con `state = 'closed'` y `closed_at IS NOT NULL`.
  - Si un issue fue reabierto y vuelto a cerrar, se toma el último `closed_at`.
  - Se descartan del cálculo de promedios los registros con $LT < 0$ (inconsistencias temporales).
## 2. Cycle Time de Atención Inicial ($CT_{first\_response}$)
- **Definición:** Tiempo transcurrido desde la creación del issue hasta la primera interacción o asignación de un desarrollador.
- **Unidad:** Horas.
- **Fórmula:**
  $$CT_{first\_response} = \frac{\min(\text{first\_comment\_at}, \text{assigned\_at}) - \text{created\_at}}{3600}$$

## 3. Throughput Semanal ($TP_{weekly}$)
- **Definición:** Cantidad total de unidades de trabajo (issues resueltos o pull requests fusionados) entregadas en una ventana de tiempo de 7 días.
- **Unidad:** Unidades cerradas / semana.
- **Fórmula:**
  $$TP_{semana}(w) = \sum_{i \in \text{Issues}} \mathbb{I}(\text{closed\_at}(i) \in \text{Semana } w)$$

## 4. Tasa de Cierre de Trabajo (*Close Rate* - $CR$)
- **Definición:** Proporción entre la cantidad de issues resueltos y la cantidad de issues creados en un período determinado.
- **Unidad:** Porcentaje ($0.0\%$ a $100.0\%+$).
- **Fórmula:**
  $$CR = \left( \frac{\text{Total Issues Cerrados en el Período}}{\text{Total Issues Creados en el Período}} \right) \times 100$$
- **Interpretación:**
  - $CR = 100\%$: Capacidad de atención balanceada con la demanda.
  - $CR < 100\%$: Acumulación de deuda técnica o desborde de requerimientos.
  - $CR > 100\%$: Reducción de backlog pendiente.

## 5. Frecuencia y Concentración de Commits ($CF$)
- **Definición:** Distribución de commits por autor, día de la semana y hora del día.
- **Métricas secundarias:**
  - Commits por estudiante / colaborador por semana.
  - Total de líneas alteradas ($\text{additions} + \text{deletions}$).

