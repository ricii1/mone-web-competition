/** Single place for the star display rule. Passing (>= 70%) = 1 star, >= 85% = 2, 100% = 3. */
export function starsFor(percent: number): 0 | 1 | 2 | 3 {
  if (percent >= 100) return 3;
  if (percent >= 85) return 2;
  if (percent >= 70) return 1;
  return 0;
}
