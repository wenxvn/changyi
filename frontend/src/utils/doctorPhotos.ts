let indexPromise: Promise<Record<string, string>> | null = null;

export async function doctorPhotoVariants(url?: string) {
  if (!url) return null;
  indexPromise ??= import("../data/doctor-photo-variants.json").then(module => module.default as Record<string, string>);
  const sourceHashes = await indexPromise;
  let decoded = url;
  try { decoded = decodeURIComponent(url); } catch { /* Unmapped URL retains the original fallback. */ }
  const hash = sourceHashes[decoded];
  if (!hash) return null;
  const root = `/static/images/doctor-variants/${hash}`;
  return { small: `${root}-80.webp`, medium: `${root}-160.webp`, large: `${root}-320.webp` };
}
