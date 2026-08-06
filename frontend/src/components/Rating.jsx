import { StarIcon } from './Icons';

// Estrellas de calificación. Antes se dibujaban con los caracteres ★/☆, que
// dependen de la fuente del sistema; ahora son SVG y heredan el color por CSS.
export function Stars({ value, size = 15 }) {
  const full = Math.round(Number(value) || 0);
  return (
    <span className="stars" aria-hidden="true">
      {[1, 2, 3, 4, 5].map((n) => (
        <StarIcon key={n} filled={n <= full} width={size} height={size} strokeWidth={1.5} />
      ))}
    </span>
  );
}

export default function Rating({ value, count, size = 15, emptyLabel = 'Sin reseñas aún' }) {
  if (value == null) {
    return <span className="rating-empty">{emptyLabel}</span>;
  }
  const numeric = Number(value);
  return (
    <span className="rating">
      <Stars value={numeric} size={size} />
      <strong>{numeric.toFixed(1)}</strong>
      {count > 0 && (
        <span className="rating-count">
          ({count} {count === 1 ? 'reseña' : 'reseñas'})
        </span>
      )}
      <span className="sr-only">{numeric.toFixed(1)} de 5 estrellas</span>
    </span>
  );
}
