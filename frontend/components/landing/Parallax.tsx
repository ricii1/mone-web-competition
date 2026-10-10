"use client";

import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";

/**
 * Moves its children vertically at a fraction of the scroll speed for a depth effect.
 * Negative speed drifts up as you scroll down. Disabled for reduced motion.
 */
export default function Parallax({
  children,
  speed = 0.15,
  className = "",
  style,
}: {
  children: ReactNode;
  speed?: number;
  className?: string;
  style?: CSSProperties;
}) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      if (ref.current) ref.current.style.transform = `translate3d(0, ${Math.round(window.scrollY * speed)}px, 0)`;
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [speed]);

  return (
    <div ref={ref} className={className} style={style}>
      {children}
    </div>
  );
}
