// Iconos SVG inline (trazos estilo Lucide/Heroicons, stroke 2, 24x24).
// Sustituyen a los emojis como iconos estructurales: los emojis dependen de la
// fuente del sistema y no se pueden tematizar con CSS; estos heredan currentColor.
const base = {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

export const SearchIcon = (props) => (
  <svg {...base} {...props}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
);

export const GraduationCapIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M22 10 12 5 2 10l10 5 10-5Z" />
    <path d="M6 12v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5" />
  </svg>
);

export const UserIcon = (props) => (
  <svg {...base} {...props}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" /></svg>
);

export const PlayIcon = (props) => (
  <svg {...base} {...props}><polygon points="6 3 20 12 6 21 6 3" /></svg>
);

export const CertificateIcon = (props) => (
  <svg {...base} {...props}>
    <circle cx="12" cy="9" r="5" />
    <path d="m8.5 13.5-2 7 5.5-3 5.5 3-2-7" />
  </svg>
);

export const FlameIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 2c1 4-4 6-4 11a6 6 0 0 0 12 0c0-3-1.5-5-3-7-1 2-2 2.5-3 2-1.2-.6-1.5-3-2-6Z" />
  </svg>
);

export const CameraIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8Z" />
    <circle cx="12" cy="13" r="4" />
  </svg>
);

export const PencilIcon = (props) => (
  <svg {...base} {...props}><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3Z" /></svg>
);

export const SparklesIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8" />
  </svg>
);

// `filled` rellena la estrella (calificación conseguida); sin él queda el contorno.
export const StarIcon = ({ filled = false, ...props }) => (
  <svg {...base} fill={filled ? 'currentColor' : 'none'} {...props}>
    <path d="m12 3 2.6 5.6 6 .8-4.4 4.3 1.1 6.1L12 17l-5.3 2.8 1.1-6.1L3.4 9.4l6-.8L12 3Z" />
  </svg>
);

export const CheckIcon = (props) => (
  <svg {...base} {...props}><path d="m4 12.5 5 5L20 6.5" /></svg>
);

export const CheckCircleIcon = (props) => (
  <svg {...base} {...props}><circle cx="12" cy="12" r="9" /><path d="m8 12.2 2.8 2.8L16 9.6" /></svg>
);

export const CircleIcon = (props) => (
  <svg {...base} {...props}><circle cx="12" cy="12" r="9" /></svg>
);

export const XIcon = (props) => (
  <svg {...base} {...props}><path d="M6 6l12 12M18 6 6 18" /></svg>
);

export const HeartIcon = ({ filled = false, ...props }) => (
  <svg {...base} fill={filled ? 'currentColor' : 'none'} {...props}>
    <path d="M12 20s-7-4.5-7-9.5A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 7 3.5c0 5-7 9.5-7 9.5Z" />
  </svg>
);

export const CartIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M2 3h2.5l2.2 11.4a2 2 0 0 0 2 1.6h7.6a2 2 0 0 0 2-1.6L20 7H6" />
    <circle cx="9.5" cy="20" r="1.4" /><circle cx="17" cy="20" r="1.4" />
  </svg>
);

export const TrophyIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
    <path d="M7 6H4v1.5A3.5 3.5 0 0 0 7.5 11M17 6h3v1.5a3.5 3.5 0 0 1-3.5 3.5" />
    <path d="M12 14v4M8.5 21h7" />
  </svg>
);

export const ClipboardIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M9 4h6v3H9V4Z" />
    <path d="M9 5.5H6.5A1.5 1.5 0 0 0 5 7v12.5A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V7a1.5 1.5 0 0 0-1.5-1.5H15" />
  </svg>
);

export const RefreshIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M20 11a8 8 0 0 0-14-4.5L4 9M4 13a8 8 0 0 0 14 4.5L20 15" />
    <path d="M4 5v4h4M20 19v-4h-4" />
  </svg>
);

export const ChartIcon = (props) => (
  <svg {...base} {...props}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>
);

export const VideoIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="2.5" y="6" width="13" height="12" rx="2" />
    <path d="m15.5 12 6-3.5v11l-6-3.5" />
  </svg>
);

export const LockIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="4" y="10.5" width="16" height="10" rx="2" />
    <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
  </svg>
);

export const CreditCardIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="2.5" y="5" width="19" height="14" rx="2" />
    <path d="M2.5 10h19M6 15h4" />
  </svg>
);

export const WalletIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M3 7a2 2 0 0 1 2-2h12v4" />
    <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9H5a2 2 0 0 1-2-2Z" />
    <circle cx="17" cy="14" r="1.2" />
  </svg>
);

export const MenuIcon = (props) => (
  <svg {...base} {...props}><path d="M4 7h16M4 12h16M4 17h16" /></svg>
);

export const ArrowLeftIcon = (props) => (
  <svg {...base} {...props}><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
);

export const ClockIcon = (props) => (
  <svg {...base} {...props}><circle cx="12" cy="12" r="9" /><path d="M12 7v5.2l3.2 2" /></svg>
);
