/**
 * Precio de un curso, respetando la promoción vigente.
 *
 * Existe como componente único porque el precio se muestra en cinco pantallas
 * (catálogo, detalle, carrito, checkout y wishlist) y si alguna mostrara el de
 * lista mientras el checkout cobra el rebajado, parecería un error de cobro.
 *
 * `curso` debe traer price, effective_price, is_on_promo y promo_discount_pct.
 */
export default function Precio({ curso, tamano = 18, mostrarEtiqueta = true }) {
  if (!curso?.is_on_promo) {
    return (
      <strong style={{ fontSize: tamano, color: 'var(--accent-strong)' }}>
        ${curso?.effective_price ?? curso?.price}
      </strong>
    );
  }

  return (
    <span className="promo-precios">
      <strong style={{ fontSize: tamano }}>${curso.effective_price}</strong>
      <s>${curso.price}</s>
      {mostrarEtiqueta && (
        <span className="badge" style={{ background: 'var(--danger-soft)', color: '#991B1B' }}>
          −{curso.promo_discount_pct}%
        </span>
      )}
    </span>
  );
}
