import type { ReactNode } from "react";

/** Tiny playful icon set: inline SVG, rounded strokes, inherits color via currentColor. */
export interface IconProps {
  size?: number;
  className?: string;
}

function make(paths: ReactNode, opts: { fill?: boolean } = {}) {
  return function Icon({ size = 24, className }: IconProps) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={opts.fill ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth={opts.fill ? 1.5 : 2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
        className={className}
      >
        {paths}
      </svg>
    );
  };
}

export const StarIcon = make(<path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.1l-5.6 3.1 1.1-6.3L2.9 9.5l6.3-.9z" />, { fill: true });
export const StarOutlineIcon = make(<path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.1l-5.6 3.1 1.1-6.3L2.9 9.5l6.3-.9z" />);
export const TrophyIcon = make(
  <>
    <path d="M7 4h10v5a5 5 0 0 1-10 0z" />
    <path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3M12 14v3M8 20h8M9 17h6v3H9z" />
  </>
);
export const BookIcon = make(
  <>
    <path d="M12 6c-2-1.5-5-2-8-1.5v13c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5v-13C17 4 14 4.5 12 6z" />
    <path d="M12 6v13" />
  </>
);
export const RocketIcon = make(
  <>
    <path d="M12 3c3.5 2 5 6 4 11l-4 3-4-3c-1-5 .500-9 4-11z" />
    <circle cx="12" cy="9.5" r="1.8" />
    <path d="M8 14l-3 2 1 3 3-1M16 14l3 2-1 3-3-1M12 18v3" />
  </>
);
export const LockIcon = make(
  <>
    <rect x="5" y="10.5" width="14" height="10" rx="3" />
    <path d="M8 10.500V8a4 4 0 0 1 8 0v2.500M12 14.500v2.5" />
  </>
);
export const CheckIcon = make(<path d="M4.5 12.500l5 5 10-11" />);
export const CrossIcon = make(<path d="M6 6l12 12M18 6L6 18" />);
export const FlagIcon = make(
  <>
    <path d="M6 21V4" />
    <path d="M6 4.500c4-2 6 2 12 0v9c-6 2-8-2-12 0" />
  </>
);
export const LightbulbIcon = make(
  <>
    <path d="M9 17.500h6M10 21h4" />
    <path d="M12 3a6 6 0 0 0-3.5 10.900c.700.6 1 1.2 1 2.100h5c0-.900.3-1.5 1-2.100A6 6 0 0 0 12 3z" />
  </>
);
export const ClockIcon = make(
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3.5 2" />
  </>
);
export const HeartIcon = make(<path d="M12 20.500S3.5 15 3.5 8.800A4.6 4.6 0 0 1 12 6.500a4.6 4.6 0 0 1 8.5 2.300C20.5 15 12 20.5 12 20.500z" />, { fill: true });
export const SparklesIcon = make(
  <>
    <path d="M10 4l1.6 4.400L16 10l-4.4 1.600L10 16l-1.6-4.400L4 10l4.4-1.600z" />
    <path d="M18 14l.800 2.200L21 17l-2.2.800L18 20l-.800-2.200L15 17l2.2-.800z" />
  </>
);
export const HomeIcon = make(
  <>
    <path d="M3.5 11.500L12 4l8.5 7.5" />
    <path d="M6 10v9.500h12V10M10 19.500v-5h4v5" />
  </>
);
export const ArrowLeftIcon = make(<path d="M19 12H5M11 5l-7 7 7 7" />);
export const ArrowRightIcon = make(<path d="M5 12h14M13 5l7 7-7 7" />);
export const PlayIcon = make(<path d="M7 4.500v15l12-7.500z" />, { fill: true });
export const MedalIcon = make(
  <>
    <circle cx="12" cy="15" r="5.5" />
    <path d="M8.5 10L6.5 3h4l1.5 4 1.5-4h4l-2 7" />
    <path d="M12 12.500l.900 1.8 2 .300-1.4 1.4.300 2-1.8-1-1.8 1 .300-2-1.4-1.4 2-.300z" />
  </>
);
export const CrownIcon = make(<path d="M3.5 8l4.5 4 4-7 4 7 4.5-4-1.5 11h-14z" />, { fill: true });
export const MapIcon = make(
  <>
    <path d="M3 6.500l6-2.5 6 2.5 6-2.500v13.500l-6 2.5-6-2.5-6 2.500z" />
    <path d="M9 4v13.500M15 6.500V20" />
  </>
);
export const PencilIcon = make(<path d="M4 20l1-4.500L16.5 4a2.1 2.1 0 0 1 3 3L8 18.500zM14.5 6l3 3" />);
export const TrashIcon = make(<path d="M4 7h16M9 7V4.500h6V7M6.5 7l1 13h9l1-13M10 11v6M14 11v6" />);
export const PlusIcon = make(<path d="M12 5v14M5 12h14" />);
export const UsersIcon = make(
  <>
    <circle cx="9" cy="8.5" r="3.5" />
    <path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 5.500a3.5 3.5 0 0 1 0 6.500M18 14.500c2.1.700 3.5 2.7 3.5 5.5" />
  </>
);
export const EyeIcon = make(
  <>
    <path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </>
);
export const EyeOffIcon = make(
  <>
    <path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7S2 12 2 12z" />
    <path d="M4 4l16 16" />
  </>
);
export const LogoutIcon = make(<path d="M10 4H5v16h5M16 8l4 4-4 4M20 12H9" />);
export const TargetIcon = make(
  <>
    <circle cx="12" cy="12" r="8" />
    <circle cx="12" cy="12" r="3" />
    <path d="M12 1.500v3M12 19.500v3M1.5 12h3M19.5 12h3" />
  </>
);
export const RefreshIcon = make(<path d="M20 11a8 8 0 0 0-14-4.500L4 9M4 4v5h5M4 13a8 8 0 0 0 14 4.500L20 15M20 20v-5h-5" />);
export const UploadIcon = make(<path d="M12 16V4M7 9l5-5 5 5M4 17v3h16v-3" />);
export const FileIcon = make(
  <>
    <path d="M6 3h8l4 4v14H6z" />
    <path d="M14 3v4h4M9 13h6M9 17h6" />
  </>
);
export const ScrollIcon = make(
  <>
    <path d="M8 4h11v13a3 3 0 0 1-3 3H6a3 3 0 0 0 3-3V6a2 2 0 0 0-1-2z" />
    <path d="M8 4a2 2 0 0 0-4 0v2h4M12 9h4M12 13h4" />
  </>
);
export const MonsterIcon = make(
  <>
    <path d="M4 20V11a8 8 0 0 1 16 0v9l-3-2-2.5 2-2.5-2-2.5 2-2.5-2z" />
    <path d="M8 3L6.5 6M16 3l1.5 3M9 11.500h.01M15 11.500h.01M9.5 15.500l1.250-1 1.250 1 1.250-1 1.250 1" />
  </>
);
export const TriangleIcon = make(<path d="M12 4l9 16H3z" />, { fill: true });
export const DiamondIcon = make(<path d="M12 2l9 10-9 10-9-10z" />, { fill: true });
export const CircleIcon = make(<circle cx="12" cy="12" r="9" />, { fill: true });
export const SquareIcon = make(<rect x="4" y="4" width="16" height="16" rx="3" />, { fill: true });
export const BellIcon = make(<path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2h-15zM10 21h4" />);
export const QuestionIcon = make(
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.5 9.500a2.6 2.6 0 0 1 5 .8c0 1.8-2.5 2.2-2.5 4M12 17.500h.01" />
  </>
);
export const ExternalIcon = make(<path d="M14 4h6v6M20 4l-9 9M18 14v5H5V6h5" />);
