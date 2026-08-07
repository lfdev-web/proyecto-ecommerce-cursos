import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { ArrowLeftIcon, FlameIcon, GraduationCapIcon } from './Icons';

// Cuenta regresiva legible. Devuelve null si ya venció o no tiene fecha, para
// que la tarjeta simplemente no muestre el plazo en vez de un "hace 3 días".
function tiempoRestante(hasta) {
  if (!hasta) return null;
  const ms = new Date(hasta) - Date.now();
  if (ms <= 0) return null;
  const dias = Math.floor(ms / 86400000);
  if (dias >= 1) return `Termina en ${dias} ${dias === 1 ? 'día' : 'días'}`;
  const horas = Math.floor(ms / 3600000);
  if (horas >= 1) return `Quedan ${horas} h`;
  return 'Termina hoy';
}

function TarjetaOferta({ curso }) {
  const plazo = tiempoRestante(curso.promo_until);
  return (
    <Link to={`/cursos/${curso.slug}`} className="promo-tarjeta">
      <div className="promo-imagen">
        {curso.cover_image
          ? <img src={curso.cover_image} alt={curso.title} />
          : <GraduationCapIcon width={40} height={40} strokeWidth={1.5} />}
        <span className="promo-etiqueta">−{curso.promo_discount_pct}%</span>
      </div>
      <div className="promo-cuerpo">
        <h3>{curso.title}</h3>
        <p className="promo-categoria">{curso.category?.name}</p>
        <div className="promo-precios">
          <strong>${curso.effective_price}</strong>
          <s>${curso.price}</s>
        </div>
        {plazo && <span className="promo-plazo">{plazo}</span>}
      </div>
    </Link>
  );
}

export default function PromoCarousel() {
  const [cursos, setCursos] = useState([]);
  const pista = useRef(null);
  const [puedeIzq, setPuedeIzq] = useState(false);
  const [puedeDer, setPuedeDer] = useState(false);

  useEffect(() => {
    api.get('/catalog/courses/promociones/')
      .then(({ data }) => setCursos(data))
      .catch(() => setCursos([]));
  }, []);

  // Las flechas se ocultan cuando no hay a dónde desplazarse, para no ofrecer
  // un control que no hace nada.
  const revisarFlechas = () => {
    const el = pista.current;
    if (!el) return;
    setPuedeIzq(el.scrollLeft > 8);
    setPuedeDer(el.scrollLeft + el.clientWidth < el.scrollWidth - 8);
  };

  useEffect(() => {
    revisarFlechas();
    window.addEventListener('resize', revisarFlechas);
    return () => window.removeEventListener('resize', revisarFlechas);
  }, [cursos]);

  const desplazar = (direccion) => {
    const el = pista.current;
    if (el) el.scrollBy({ left: direccion * (el.clientWidth * 0.8), behavior: 'smooth' });
  };

  if (cursos.length === 0) return null;

  return (
    <section className="promo-seccion" aria-labelledby="titulo-ofertas">
      <div className="promo-encabezado">
        <h2 id="titulo-ofertas" className="icon-text">
          <FlameIcon width={22} height={22} style={{ color: 'var(--danger)' }} />
          Ofertas por tiempo limitado
        </h2>
        <div className="promo-flechas">
          <button
            type="button" onClick={() => desplazar(-1)}
            disabled={!puedeIzq} aria-label="Ver ofertas anteriores"
          >
            <ArrowLeftIcon width={18} height={18} />
          </button>
          <button
            type="button" onClick={() => desplazar(1)}
            disabled={!puedeDer} aria-label="Ver más ofertas"
          >
            <ArrowLeftIcon width={18} height={18} style={{ transform: 'rotate(180deg)' }} />
          </button>
        </div>
      </div>

      <div className="promo-pista" ref={pista} onScroll={revisarFlechas}>
        {cursos.map((c) => <TarjetaOferta key={c.id} curso={c} />)}
      </div>
    </section>
  );
}
