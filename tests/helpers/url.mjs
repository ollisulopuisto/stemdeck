// Keep mock routing and request assertions strict: look-alike domains must not
// receive Wikipedia fixture responses or count as Wikipedia requests.
export function isWikipediaUrl(value) {
  const url = value instanceof URL ? value : new URL(value);
  return url.protocol === "https:" && !url.username && !url.password && !url.port
    && /^[a-z-]+\.wikipedia\.org$/.test(url.hostname);
}
