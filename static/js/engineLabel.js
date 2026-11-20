// Separation engine helpers: the label on a library card and the state of the
// Settings engine row. Pure functions, so they can be tested without a DOM.

/**
 * The badge a library card shows for the engine that separated it.
 * Default Demucs jobs show nothing, since forty identical badges say nothing.
 * @returns {string} the label, or "" when there is nothing to say
 */
export function engineBadgeLabel(track, t) {
  if (!track) return "";
  if (track.engineFallback) return t("engine.badge.fallback");
  if (track.separationEngine === "roformer-sw") return t("engine.badge.roformer");
  return "";
}

/**
 * Which state the Settings engine row is in.
 * One of: "intel", "unavailable", "failed", "downloading", "in-use", "default".
 */
export function engineRowState(settings) {
  const status = settings?.separation_engine_status || {};
  const reason = status.roformer_unavailable_reason;
  if (reason === "intel-mac") return "intel";
  if (reason) return "unavailable";
  if (settings?.separation_engine === "roformer-sw") {
    if (status.downloading) return "downloading";
    if (status.last_failure) return "failed";
    return "in-use";
  }
  if (status.last_failure) return "failed";
  return "default";
}

/** Download progress as a whole percent, never 100 until the model is ready. */
export function engineDownloadPercent(status) {
  const total = Number(status?.model_total_bytes) || 0;
  const got = Number(status?.model_bytes) || 0;
  if (!total || got <= 0) return 0;
  return Math.min(99, Math.floor((got / total) * 100));
}
