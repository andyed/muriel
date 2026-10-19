/** Deterministic illustration data, never observations of an actual ecosystem. */
export const HABITATS = ['Reedbed', 'Upland', 'Shore'];
export const DOMAIN = Object.freeze({ x: [0, 32], y: [0, 100] });
export const records = Object.freeze(Array.from({ length: 192 }, (_, i) => {
  const day = Math.floor(i / 6);
  const habitat = HABITATS[i % 3];
  const wave = Math.sin(day * .38 + (i % 3) * 1.4);
  const pulse = day >= 15 && day <= 20 && habitat === 'Reedbed' ? 28 : 0;
  return Object.freeze({
    id: `F${String(i + 1).padStart(3, '0')}`,
    x: day + .12 + (i % 6) * .15,
    day: day + 1,
    habitat,
    detections: Math.round(Math.max(5, Math.min(96, 35 + (i % 3) * 9 + wave * 16 + ((i * 17) % 13) + pulse))),
    confidence: 72 + ((i * 7 + day * 3) % 28),
    station: `${habitat.slice(0, 1)}${1 + (i % 2)}`,
  });
}));
